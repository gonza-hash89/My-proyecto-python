"""
brain/intent_patterns.py - Matcher de patrones regex (SEMANA 4, FASE 2)

Sistema rápido de reconocimiento de intenciones basado en regex.

- 52 intenciones, 468+ patrones en español e inglés
- Detección automática de idioma (langdetect + lexicón de respaldo)
- Velocidad objetivo: <5ms por consulta
- Interfaz: PatternMatcher().match(text) -> list[PatternMatch]

Flujo:
    1. detect_language(text) -> "es" | "en" | "mixed"
    2. Se prueban los patrones del idioma detectado (y del otro como fallback)
    3. Cada coincidencia genera PatternMatch(score, intent, entities_brutas)
"""

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from brain.intent_data import INTENT_CATALOG

try:
    from langdetect import detect
    _LANGDETECT_AVAILABLE = True
except Exception:  # pragma: no cover - entorno sin langdetect
    _LANGDETECT_AVAILABLE = False

logger = logging.getLogger("Jarvis.PatternMatcher")


# Stopwords excluidas como triggers (evitan candidatos inflados)
_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "have", "you",
    "que", "los", "las", "para", "con", "por", "una", "uno", "unas", "unos",
    "como", "cuando", "donde", "porque", "what", "how", "why",
}


# ─────────────────────────────────────────────────────────────
# Detección de idioma
# ─────────────────────────────────────────────────────────────

# Palabras fuertemente asociadas a cada idioma (fallback del lexicón)
_LANG_LEXICON = {
    "es": {
        "qué", "cuál", "cómo", "dónde", "cuándo", "quién", "hora", "fecha", "clima",
        "ayuda", "salir", "música", "canción", "chiste", "película", "luces", "puerta",
        "temporizador", "recuérdame", "por favor", "la", "el", "los", "las", "un",
        "una", "para", "con", "sobre", "tengo", "quiero", "abre", "apaga", "enciende",
        "envía", "manda", "transfiere", "dinero", "soles", "dólares", "saldo", "cuenta",
        "cortinas", "cámara", "alarma", "equipo", "noticias", "presupuesto", "viaje",
        "hoy", "ayer", "mañana", "hace", "mucho", "frío", "dame",
        "necesito", "está", "es", "son", "estoy", "tengo", "este", "esta", "estas",
        "esto", "cuánto", "cuántos", "mi", "mis", "tu", "tus", "quién", "lluvia",
    },
    "en": {
        "what", "when", "where", "who", "how", "why", "time", "date", "weather",
        "help", "exit", "music", "song", "joke", "movie", "lights", "door",
        "timer", "remind", "please", "the", "a", "an", "for", "with", "about",
        "have", "want", "open", "turn", "play", "me", "my",
    },
}


def detect_language(text: str) -> str:
    """Detecta el idioma de la frase: 'es', 'en' o 'mixed'.

    Vía principal: lexicón de palabras (microsegundos).
    Fallback: langdetect solo cuando el lexicón no decide (frases ambiguas).
    """
    sample = text.strip().lower()
    if not sample:
        return "es"

    words = set(re.findall(r"[a-záéíóúñü]+", sample))
    es_hits = len(words & _LANG_LEXICON["es"])
    en_hits = len(words & _LANG_LEXICON["en"])

    if es_hits > en_hits:
        return "es"
    if en_hits > es_hits:
        return "en"

    # Empate o sin pistas: usar langdetect como respaldo
    if _LANGDETECT_AVAILABLE:
        try:
            detected = detect(sample)
            if detected in ("es", "en"):
                return detected
        except Exception:
            pass

    return "mixed"


# ─────────────────────────────────────────────────────────────
# Resultado del matching
# ─────────────────────────────────────────────────────────────

@dataclass
class PatternMatch:
    """Coincidencia de un patrón con el texto."""
    intent: str
    score: float
    matched_pattern: str
    language: str
    raw: str

    def __repr__(self) -> str:
        return f"PatternMatch(intent={self.intent}, score={self.score:.2f}, lang={self.language})"


# ─────────────────────────────────────────────────────────────
# Matcher
# ─────────────────────────────────────────────────────────────

class PatternMatcher:
    """
    Compila y ejecuta patrones regex del catálogo.

    Uso:
        matcher = PatternMatcher()
        matches = matcher.match("¿qué hora es?")
    """

    def __init__(self) -> None:
        self._compiled: Dict[str, List] = {}
        self._triggers: Dict[str, set] = {}
        self._always_candidate: set = set()
        self._compile_all()
        self._match_times_ms: List[float] = []
        self.logger = logger

    def _compile_all(self) -> None:
        """Compila los patrones de cada intención por idioma y construye el índice de triggers."""
        for name, intent in INTENT_CATALOG.items():
            compiled_es = [re.compile(p, re.IGNORECASE) for p in intent["patterns_es"]]
            compiled_en = [re.compile(p, re.IGNORECASE) for p in intent["patterns_en"]]
            self._compiled[name] = {"es": compiled_es, "en": compiled_en}

            # Triggers: palabras literales de patrones + variaciones (len >= 3, sin stopwords)
            triggers = self._collect_triggers(intent)
            if not triggers:
                self._always_candidate.add(name)
            for token in triggers:
                self._triggers.setdefault(token, set()).add(name)

    @staticmethod
    def _collect_triggers(intent: Dict[str, object]) -> set:
        """Extrae tokens de activación (palabras literales) de patrones y variaciones."""
        tokens = set()
        sources = []
        sources.extend(intent["patterns_es"])
        sources.extend(intent["patterns_en"])
        sources.extend(intent["variations_es"])
        sources.extend(intent["variations_en"])
        for source in sources:
            for word in re.findall(r"[a-záéíóúñü]+", source.lower()):
                if len(word) >= 3 and word not in _STOPWORDS:
                    tokens.add(word)
        return tokens

    def _get_candidates(self, lower_text: str) -> set:
        """Intenciones candidatas según los tokens presentes en el texto."""
        words = {w for w in re.findall(r"[a-záéíóúñü]+", lower_text) if len(w) >= 3}
        candidates = set(self._always_candidate)
        for word in words:
            candidates |= self._triggers.get(word, set())
        return candidates

    # ── API pública ──

    def match(self, text: str, language: Optional[str] = None) -> List[PatternMatch]:
        """
        Retorna todas las coincidencias de patrones, ordenadas por score desc.

        Args:
            text: texto del usuario.
            language: fuerza idioma; si es None se detecta.

        Returns:
            Lista de PatternMatch (vacía si no hay coincidencias).
        """
        start = time.perf_counter()
        lang = language or detect_language(text)
        lower = text.lower().strip()
        matches: List[PatternMatch] = []

        candidates = self._get_candidates(lower)
        if not candidates:
            self._record_time(start)
            return matches

        # Idiomas a probar: el detectado primero, el otro después
        order = self._language_order(lang)
        for name in candidates:
            entry = self._compiled[name]
            for candidate in order:
                patterns = entry.get(candidate, [])
                for pattern in patterns:
                    if pattern.search(lower):
                        score = INTENT_CATALOG[name]["confidence"]
                        matches.append(
                            PatternMatch(
                                intent=name,
                                score=score,
                                matched_pattern=pattern.pattern,
                                language=candidate,
                                raw=text,
                            )
                        )
                        break  # una coincidencia por idioma/intención

        self._record_time(start)

        # Ordenar por score desc; a igual score gana el patrón más específico
        matches.sort(key=lambda m: (m.score, len(m.matched_pattern)), reverse=True)
        return matches

    def _record_time(self, start: float) -> None:
        """Registra el tiempo del último match (acotado a 500 muestras)."""
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self._match_times_ms.append(elapsed_ms)
        if len(self._match_times_ms) > 500:
            self._match_times_ms = self._match_times_ms[-500:]

    def match_best(self, text: str, language: Optional[str] = None) -> Optional[PatternMatch]:
        """Retorna la mejor coincidencia o None."""
        matches = self.match(text, language)
        return matches[0] if matches else None

    # ── Introspección / métricas ──

    def detect_language(self, text: str) -> str:
        return detect_language(text)

    def get_intent_count(self) -> int:
        return len(self._compiled)

    def get_pattern_count(self) -> int:
        return sum(
            len(v["es"]) + len(v["en"]) for v in self._compiled.values()
        )

    def avg_match_time_ms(self) -> float:
        """Tiempo promedio de matching (ms)."""
        if not self._match_times_ms:
            return 0.0
        return sum(self._match_times_ms) / len(self._match_times_ms)

    def median_match_time_ms(self) -> float:
        """Mediana (P50) de matching en ms; robusta a picos del sistema."""
        if not self._match_times_ms:
            return 0.0
        ordered = sorted(self._match_times_ms)
        n = len(ordered)
        mid = n // 2
        if n % 2:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2.0

    def clear_times(self) -> None:
        self._match_times_ms = []

    @staticmethod
    def _language_order(lang: str) -> List[str]:
        """Orden de idiomas a probar según la detección."""
        if lang == "en":
            return ["en", "es"]
        if lang == "es":
            return ["es", "en"]
        return ["es", "en"]  # mixed: probar ambos, español primero
