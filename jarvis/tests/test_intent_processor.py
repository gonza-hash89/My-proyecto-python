"""
Tests de brain/intent_processor.py (FASE 5)

Verifica:
- Resultado completo (IntentResult) y compatibilidad con recognize()
- Camino de patrones (method="pattern") para comandos conocidos
- Camino ML (method="ml") cuando no hay patrón
- Extracción de entidades en el resultado final
- Estadísticas y singleton
"""

from brain.intent_processor import IntentProcessor, get_processor, IntentResult
from brain.intent_data import INTENT_CATALOG


def _reset_and_process(text):
    proc = get_processor()
    proc.reset_stats()
    return proc, proc.process(text)


def test_resulta_intentresult():
    proc, result = _reset_and_process("¿qué hora es?")
    assert isinstance(result, IntentResult)
    assert result.intent == "time_query"
    assert result.name == "time_query"
    assert 0 <= result.confidence <= 1
    assert result.raw_input == "¿qué hora es?"
    assert result.language == "es"
    assert result.alternatives


def test_camino_patron_alta_confianza():
    proc, result = _reset_and_process("dame la fecha")
    assert result.method == "pattern"
    assert result.intent == "date_query"
    assert result.confidence >= 0.9


def test_camino_ml_sin_patron():
    proc, result = _reset_and_process("las patatas vuelan de noche y sonríen")
    assert result.method in ("ml", "hybrid")
    assert result.intent in INTENT_CATALOG


def test_entidades_en_resultado():
    proc, result = _reset_and_process("envía 100 soles a María")
    assert result.intent == "transfer_money"
    assert result.entities.get("amount") == "100"
    assert "mar" in result.entities.get("recipient", "").lower() or \
        result.entities.get("recipient") == "María"


def test_reconoce_varios_comandos():
    proc = get_processor()
    casos = {
        "tell me a joke": "tell_joke",
        "turn on the lights": "lights_on",
        "cuál es mi saldo": "check_balance",
        "abre youtube": "watch_videos",
    }
    for frase, esperado in casos.items():
        result = proc.process(frase)
        assert result.intent == esperado, (frase, result)


def test_recognize_compatible():
    proc = get_processor()
    result = proc.recognize("¿qué hora es?")
    assert result.name == "time_query"
    assert hasattr(result, "confidence")
    assert hasattr(result, "entities")
    assert hasattr(result, "raw_input")


def test_estadisticas_acumulan():
    proc = get_processor()
    proc.reset_stats()
    proc.process("¿qué hora es?")
    proc.process("¿qué hora es?")
    stats = proc.get_stats()
    assert stats["queries"] == 2
    assert stats["by_method"]["pattern"] >= 2
    assert stats["intents_available"] == len(INTENT_CATALOG)


def test_estadisticas_reset():
    proc = get_processor()
    proc.reset_stats()
    proc.process("¿qué hora es?")
    proc.reset_stats()
    assert proc.get_stats()["queries"] == 0
    assert sum(proc.get_stats()["by_method"].values()) == 0


def test_singleton():
    assert get_processor() is get_processor()


def test_puede_construirse_inyectando():
    proc = IntentProcessor()
    assert proc.pattern_matcher.get_intent_count() == len(INTENT_CATALOG)
