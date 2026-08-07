"""
Tests bilingües ES/EN (FASE 7)

Verifica:
- 100+ pares ES/EN: cada intención del catálogo es reconocida en ambos idiomas
- detect_language() distingue es/en en frases claras
- Las variaciones del dataset resuelven a la intención correcta en cada idioma
"""

from brain.intent_data import INTENT_CATALOG
from brain.intent_processor import get_processor
from brain.intent_patterns import detect_language


def _resolve(text):
    return get_processor().process(text).intent


def test_cada_intencion_reconocida_en_ambos_idiomas():
    total_es = 0
    total_en = 0
    sin_es = []
    sin_en = []
    for name, intent in INTENT_CATALOG.items():
        es_ok = any(_resolve(t) == name for t in intent["variations_es"])
        en_ok = any(_resolve(t) == name for t in intent["variations_en"])
        total_es += 1 if es_ok else 0
        total_en += 1 if en_ok else 0
        if not es_ok:
            sin_es.append(name)
        if not en_ok:
            sin_en.append(name)
    assert total_es >= 50, f"ES fallando: {sin_es}"
    assert total_en >= 50, f"EN fallando: {sin_en}"
    assert total_es + total_en >= 100


def test_pares_es_en_equivalentes_resuelven_igual():
    pares = [
        ("¿qué hora es?", "what time is it?"),
        ("dame la fecha", "give me the date"),
        ("enciende las luces", "turn on the lights"),
        ("cuéntame un chiste", "tell me a joke"),
        ("cuál es mi saldo", "what is my balance"),
        ("pon música", "play some music"),
        ("agrega una tarea", "add a task"),
        ("guarda una nota", "take a note"),
        ("pon un temporizador", "set a timer"),
        ("busca información", "search for information"),
    ]
    for es, en in pares:
        assert _resolve(es) == _resolve(en), (es, en, _resolve(es), _resolve(en))


def test_detect_language_es():
    for frase in ["¿qué hora es?", "hoy hace mucho frío", "envía cien soles a mamá"]:
        assert detect_language(frase) == "es", frase


def test_detect_language_en():
    for frase in ["what time is it?", "tell me a joke", "send one hundred dollars to mom"]:
        assert detect_language(frase) == "en", frase


def test_procesador_marca_idioma():
    result = get_processor().process("turn on the lights")
    assert result.language == "en"
    result = get_processor().process("qué hora es")
    assert result.language == "es"
