"""
brain/intent_processor.py - Reconocedor HÍBRIDO de intenciones (SEMANA 4, FASE 5)

Fusión de las tres piezas de las fases previas:
    1. PatternMatcher (regex): rápido y preciso para comandos conocidos.
    2. IntentMLModel (MultinomialNB + TF-IDF de palabras): generaliza lo que no matchea.
    3. EntityExtractor: entidades (slots) de la intención ganadora.

Estrategia de fusión:
    - Se combina cada candidato: score = PATTERN_WEIGHT * conf_patron + ML_WEIGHT * prob_ml.
    - Si el mejor patrón tiene confianza >= PATTERN_HIGH y coincide con el mejor
      candidato combinado -> method="pattern" (camino rápido).
    - Sin coincidencia de patrones -> method="ml".
    - Cualquier otra cosa (desacuerdo o baja confianza de patrón) -> method="hybrid".

Compatibilidad:
    - process(text) -> IntentResult (nuevo)
    - recognize(text) -> alias de process (misma firma que core/intent_recognizer)

Singleton:
    - get_processor() devuelve una instancia reutilizable (ML se auto-entrena al
      primer uso si no hay modelo persistido).
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from brain.intent_entities import EntityExtractor
from brain.intent_ml import IntentMLModel
from brain.intent_patterns import PatternMatcher, detect_language

logger = logging.getLogger("Jarvis.IntentProcessor")

PATTERN_WEIGHT = 0.6
ML_WEIGHT = 0.4
PATTERN_HIGH = 0.90


@dataclass
class IntentResult:
    """Resultado del reconocimiento híbrido."""
    intent: str
    confidence: float
    entities: Dict[str, str]
    raw_input: str
    method: str = "ml"
    language: str = "es"
    latency_ms: float = 0.0
    alternatives: List[Tuple[str, float]] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Alias de compatibilidad con core/intent_recognizer.Intent."""
        return self.intent

    def __repr__(self) -> str:
        return (
            f"IntentResult(intent={self.intent}, confidence={self.confidence:.2f}, "
            f"method={self.method}, lang={self.language})"
        )


class IntentProcessor:
    """Orquesta patrones + ML + entidades para reconocer una intención."""

    def __init__(
        self,
        pattern_matcher: Optional[PatternMatcher] = None,
        ml_model: Optional[IntentMLModel] = None,
        entity_extractor: Optional[EntityExtractor] = None,
    ) -> None:
        self.pattern_matcher = pattern_matcher or PatternMatcher()
        self.ml_model = ml_model or IntentMLModel()
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.logger = logger

        # Estadísticas
        self._queries = 0
        self._method_counts: Dict[str, int] = {"pattern": 0, "ml": 0, "hybrid": 0}
        self._latency_sum_ms = 0.0
        self._pattern_ms_sum = 0.0
        self._ml_ms_sum = 0.0

    # ── API principal ──

    def process(self, text: str) -> IntentResult:
        """Reconoce la intención de `text` usando la fusión híbrida."""
        start = time.perf_counter()

        language = detect_language(text)

        # Fase 1: patrones regex
        p_start = time.perf_counter()
        pmatches = self.pattern_matcher.match(text, language=language)
        pattern_ms = (time.perf_counter() - p_start) * 1000.0

        # Fase 2: modelo ML
        m_start = time.perf_counter()
        ml_results = self.ml_model.predict(text, top_k=5)
        ml_ms = (time.perf_counter() - m_start) * 1000.0

        # Fase 3: fusión de puntajes
        p_scores = {m.intent: m.score for m in pmatches}
        m_probs = {intent: prob for intent, prob in ml_results}

        candidates = set(p_scores) | set(m_probs)
        combined: Dict[str, float] = {}
        for cand in candidates:
            combined[cand] = (
                PATTERN_WEIGHT * p_scores.get(cand, 0.0)
                + ML_WEIGHT * m_probs.get(cand, 0.0)
            )

        best = max(combined, key=combined.get) if combined else "unknown"
        best_pattern = pmatches[0] if pmatches else None

        if best_pattern is not None and best_pattern.score >= PATTERN_HIGH \
                and best == best_pattern.intent:
            method = "pattern"
            confidence = p_scores[best]
        elif best_pattern is None:
            method = "ml"
            confidence = m_probs.get(best, 0.0)
        else:
            method = "hybrid"
            confidence = combined.get(best, 0.0)

        confidence = min(max(confidence, 0.0), 1.0)
        entities = self.entity_extractor.extract(best, text)
        alternatives = sorted(
            ((c, combined[c]) for c in candidates),
            key=lambda item: item[1],
            reverse=True,
        )[:3]

        latency_ms = (time.perf_counter() - start) * 1000.0
        self._update_stats(method, latency_ms, pattern_ms, ml_ms)

        return IntentResult(
            intent=best,
            confidence=confidence,
            entities=entities,
            raw_input=text,
            method=method,
            language=language,
            latency_ms=round(latency_ms, 3),
            alternatives=alternatives,
        )

    def recognize(self, text: str) -> IntentResult:
        """Alias de process() para compatibilidad con core/intent_recognizer."""
        return self.process(text)

    # ── Estadísticas ──

    def _update_stats(self, method: str, latency_ms: float, pattern_ms: float, ml_ms: float) -> None:
        self._queries += 1
        self._method_counts[method] += 1
        self._latency_sum_ms += latency_ms
        self._pattern_ms_sum += pattern_ms
        self._ml_ms_sum += ml_ms

    def get_stats(self) -> Dict[str, object]:
        """Estadísticas acumuladas del procesador."""
        n = max(self._queries, 1)
        return {
            "queries": self._queries,
            "by_method": dict(self._method_counts),
            "avg_latency_ms": round(self._latency_sum_ms / n, 3),
            "avg_pattern_ms": round(self._pattern_ms_sum / n, 3),
            "avg_ml_ms": round(self._ml_ms_sum / n, 3),
            "intents_available": self.pattern_matcher.get_intent_count(),
        }

    def reset_stats(self) -> None:
        self._queries = 0
        self._method_counts = {"pattern": 0, "ml": 0, "hybrid": 0}
        self._latency_sum_ms = 0.0
        self._pattern_ms_sum = 0.0
        self._ml_ms_sum = 0.0

    def __repr__(self) -> str:
        return f"IntentProcessor(intents={self.pattern_matcher.get_intent_count()})"


# ─────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────

_processor: Optional[IntentProcessor] = None


def get_processor() -> IntentProcessor:
    """Devuelve la instancia única del procesador híbrido."""
    global _processor
    if _processor is None:
        _processor = IntentProcessor()
    return _processor
