"""
Tests de brain/intent_ml.py (FASE 4)

Verifica:
- Entrenamiento y predicción
- Precisión mínima sobre el split de validación
- Persistencia (save/load) y auto-carga
- Datos bilingües y todas las intenciones cubiertas
"""

import os
import tempfile

from brain.intent_ml import IntentMLModel
from brain.intent_data import INTENT_CATALOG


def _fresh_model(tmp_path):
    """Modelo con ruta de persistencia temporal."""
    path = os.path.join(str(tmp_path), "intent_model.pkl")
    return IntentMLModel(model_path=path)


def test_entrena_y_predice(tmp_path):
    model = _fresh_model(tmp_path)
    model.train()

    best = model.predict_best("¿qué hora es?")
    assert best is not None
    assert best[0] == "time_query"
    assert 0 <= best[1] <= 1.0


def test_accuracy_minima(tmp_path):
    model = _fresh_model(tmp_path)
    model.train()
    acc = model.accuracy()
    assert acc is not None, "No se reportó accuracy"
    assert acc >= 0.88, f"Accuracy demasiado baja: {acc:.3f}"


def test_prediccion_bilingue(tmp_path):
    model = _fresh_model(tmp_path)
    model.train()
    for phrase, expected in [
        ("dame la fecha", "date_query"),
        ("tell me a joke", "tell_joke"),
        ("play some jazz", "play_music"),
        ("turn on the lights", "lights_on"),
        ("cuál es mi saldo", "check_balance"),
    ]:
        best = model.predict_best(phrase)
        assert best is not None and best[0] == expected, (phrase, best)


def test_top_k(tmp_path):
    model = _fresh_model(tmp_path)
    model.train()
    results = model.predict("qué hora es", top_k=5)
    assert 1 <= len(results) <= 5
    assert results[0][0] == "time_query"
    probs = [p for _, p in results]
    assert probs == sorted(probs, reverse=True)


def test_proba_map_cubre_todas(tmp_path):
    model = _fresh_model(tmp_path)
    model.train()
    mapa = model.predict_proba_map("cuéntame un chiste")
    assert set(mapa) == set(INTENT_CATALOG)
    assert abs(sum(mapa.values()) - 1.0) < 1e-6


def test_persistencia(tmp_path):
    model = _fresh_model(tmp_path)
    model.train()
    path = model.save()

    loaded = IntentMLModel(model_path=path)
    assert loaded.is_trained()
    best = loaded.predict_best("what time is it?")
    assert best is not None and best[0] == "time_query"


def test_load_inexistente_no_falla(tmp_path):
    model = _fresh_model(tmp_path)
    assert model.load() is False
    assert model.is_trained() is False


def test_autoentrena_al_predecir(tmp_path):
    # Sin entrenar explícitamente, predict() debe auto-entrenar
    model = _fresh_model(tmp_path)
    assert model.is_trained() is False
    best = model.predict_best("salir")
    assert best is not None
    assert model.is_trained() is True


def test_train_stats(tmp_path):
    model = _fresh_model(tmp_path)
    model.train()
    stats = model.get_train_stats()
    assert stats["samples"] >= 1000
    assert stats["intents"] == len(INTENT_CATALOG)
    assert stats["by_lang"]["es"] > 0
    assert stats["by_lang"]["en"] > 0
