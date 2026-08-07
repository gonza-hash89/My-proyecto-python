"""
brain/intent_ml.py - Modelo ML de reconocimiento de intenciones (SEMANA 4, FASE 4)

Pipeline TF-IDF por n-gramas de caracteres + LinearSVC.

Elección de diseño:
- MultinomialNB (plan inicial) no alcanzaba la meta de precisión >=88% con el
  dataset sintético bilingüe (quedaba ~83%). El análisis mostró que los n-gramas
  de caracteres (char_wb 2-4) capturan mejor la morfología ES/EN en datasets
  pequeños, y LinearSVC con ellos llega a ~90-95% de validación.
- Las "probabilidades" se obtienen por softmax sobre decision_function
  (LinearSVC no expone predict_proba), suficiente para el híbrido.

Persistencia con joblib en data/intent_model.pkl. Auto-entrenamiento y
auto-carga perezosa (lazy): el primer predict() entrena si no hay modelo.

Interfaz:
    model = IntentMLModel()
    model.train()
    model.predict("me gustaría escuchar jazz") -> [("play_music", 0.91), ...]
    model.save() / model.load()
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np
from joblib import dump, load as joblib_load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from brain.intent_data import get_training_data, training_stats

logger = logging.getLogger("Jarvis.IntentMLModel")

_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "intent_model.pkl",
)


class IntentMLModel:
    """
    Clasificador de intenciones bilingüe basado en TF-IDF (char n-grams) + LinearSVC.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or _DEFAULT_MODEL_PATH
        self._pipeline: Optional[Pipeline] = None
        self._fitted = False
        self._train_stats: Dict[str, object] = {}
        self.logger = logger

        if os.path.exists(self.model_path):
            self.load()

    # ── Entrenamiento ──

    def train(
        self,
        data: Optional[List[Dict[str, str]]] = None,
        force: bool = False,
        test_ratio: float = 0.2,
        random_state: int = 42,
    ) -> "IntentMLModel":
        """
        Entrena (o re-entrena) el modelo con el dataset.

        Args:
            data: lista de {"text", "intent", "lang"}. None -> dataset del catálogo.
            force: si False y el modelo ya está entrenado, no re-entrena.
            test_ratio: fracción de validación para reportar accuracy.
            random_state: semilla del split.

        Returns:
            self (encadenable).
        """
        if self._fitted and not force:
            return self

        dataset = data if data is not None else get_training_data()
        texts = [example["text"] for example in dataset]
        labels = [example["intent"] for example in dataset]

        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels,
            test_size=test_ratio,
            random_state=random_state,
            stratify=labels,
        )

        pipeline = Pipeline([
            ("vectorizer", TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 4),
                strip_accents="unicode",
                sublinear_tf=True,
                token_pattern=None,
            )),
            ("classifier", LinearSVC(C=1.0)),
        ])
        pipeline.fit(X_train, y_train)

        # Métricas sobre el split de validación
        score = pipeline.score(X_test, y_test)
        stats = training_stats(dataset)
        self._train_stats = {
            "samples": len(dataset),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(float(score), 4),
            "intents": stats["intents_covered"],
            "by_lang": stats["by_lang"],
        }

        self._pipeline = pipeline
        self._fitted = True
        self.logger.info(
            f"Modelo entrenado | muestras={len(dataset)} | accuracy={score:.2%}"
        )
        return self

    # ── Predicción ──

    def _ensure_ready(self) -> None:
        """Garantiza un modelo cargado/entrenado antes de predecir."""
        if self._fitted and self._pipeline is not None:
            return
        if os.path.exists(self.model_path):
            self.load()
        if not self._fitted:
            self.train()

    def _softmax(self, scores: np.ndarray) -> np.ndarray:
        """Convierte decision_function de LinearSVC a pseudo-probabilidades."""
        shifted = scores - np.max(scores)
        exp = np.exp(shifted)
        total = np.sum(exp)
        return exp / total if total > 0 else np.full_like(shifted, 0.0)

    def predict(self, text: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Predice las intenciones más probables.

        Returns:
            Lista de (intent, prob) ordenada por prob desc.
        """
        self._ensure_ready()
        pipeline = self._pipeline
        if pipeline is None:  # pragma: no cover - defensivo
            return []

        proba = self._softmax(pipeline.decision_function([text])[0])
        classes = pipeline.classes_
        ranked = np.argsort(proba)[::-1][:top_k]
        return [(str(classes[i]), float(proba[i])) for i in ranked]

    def predict_best(self, text: str) -> Optional[Tuple[str, float]]:
        """Retorna (intent, prob) de la mejor predicción o None."""
        results = self.predict(text, top_k=1)
        if not results:
            return None
        intent, prob = results[0]
        return (intent, prob)

    def predict_proba_map(self, text: str) -> Dict[str, float]:
        """Retorna un dict {intent: prob} para todas las clases."""
        self._ensure_ready()
        pipeline = self._pipeline
        if pipeline is None:  # pragma: no cover - defensivo
            return {}
        proba = self._softmax(pipeline.decision_function([text])[0])
        return {str(c): float(p) for c, p in zip(pipeline.classes_, proba)}

    # ── Métricas ──

    def accuracy(self) -> Optional[float]:
        """Accuracy reportado del último entrenamiento (split 80/20)."""
        return self._train_stats.get("accuracy")

    def get_train_stats(self) -> Dict[str, object]:
        return dict(self._train_stats)

    # ── Persistencia ──

    def save(self, path: Optional[str] = None) -> str:
        """Guarda el modelo con joblib. Retorna la ruta usada."""
        target = path or self.model_path
        if self._pipeline is None:  # pragma: no cover - defensivo
            raise ValueError("No hay modelo entrenado para guardar")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        dump({"pipeline": self._pipeline, "train_stats": self._train_stats}, target)
        self.model_path = target
        self.logger.info(f"Modelo guardado en {target}")
        return target

    def load(self, path: Optional[str] = None) -> bool:
        """Carga un modelo guardado. Retorna True si se cargó."""
        target = path or self.model_path
        if not os.path.exists(target):
            return False
        try:
            payload = joblib_load(target)
            self._pipeline = payload["pipeline"]
            self._train_stats = payload.get("train_stats", {})
            self._fitted = True
            self.model_path = target
            self.logger.info(f"Modelo cargado desde {target}")
            return True
        except Exception as exc:  # pragma: no cover - archivo corrupto
            self.logger.warning(f"No se pudo cargar el modelo ({exc})")
            return False

    def is_trained(self) -> bool:
        return self._fitted and self._pipeline is not None
