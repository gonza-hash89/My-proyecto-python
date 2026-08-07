"""
Tests de brain/intent_data.py (FASE 1)

Verifica:
- Catálogo completo: 50+ intenciones, 7 categorías, todos con patrones/variaciones ES+EN
- Dataset de entrenamiento: 1000+ ejemplos, cubre todas las intenciones e idiomas
"""

from brain.intent_data import (
    INTENT_CATALOG,
    CATEGORIES,
    catalog_stats,
    generate_training_data,
    get_intent,
    get_all_intents,
    get_categories,
    get_intents_by_category,
    get_training_data,
    training_stats,
)


# ────────── Catálogo ──────────

def test_catalogo_tiene_50_mas_intenciones():
    assert len(INTENT_CATALOG) >= 50


def test_catalogo_tiene_7_categorias():
    assert len(CATEGORIES) == 7
    assert set(INTENT_CATALOG[i]["category"] for i in INTENT_CATALOG) == set(CATEGORIES)


def test_cada_intencion_esta_completa():
    for name, intent in INTENT_CATALOG.items():
        assert intent["name"] == name
        assert intent["category"] in CATEGORIES
        assert 0 < intent["confidence"] <= 1
        assert isinstance(intent["entities"], list)
        assert intent["patterns_es"], f"{name} sin patrones ES"
        assert intent["patterns_en"], f"{name} sin patrones EN"
        assert intent["variations_es"], f"{name} sin variaciones ES"
        assert intent["variations_en"], f"{name} sin variaciones EN"


def test_nombres_unicos():
    names = [i["name"] for i in get_all_intents()]
    assert len(names) == len(set(names))


def test_categorias_tienen_conteos_esperados():
    expected = {"basicas": 10, "entretenimiento": 10, "hogar": 8,
                "finanzas": 7, "salud": 5, "productividad": 7, "viajes": 5}
    actual = {cat: len(intents) for cat, intents in get_categories().items()}
    assert actual == expected


def test_get_intent_y_filtros():
    assert get_intent("time_query") is not None
    assert get_intent("no_existe") is None
    assert len(get_intents_by_category("finanzas")) == 7
    assert get_intents_by_category("no_existe") == []


def test_stats():
    stats = catalog_stats()
    assert stats["total_intents"] == len(INTENT_CATALOG)
    assert stats["has_es"] is True
    assert stats["has_en"] is True
    assert stats["total_patterns"] > 400


# ────────── Dataset de entrenamiento ──────────

def test_dataset_mayor_a_1000():
    data = get_training_data()
    assert len(data) >= 1000


def test_dataset_cubre_todas_las_intenciones():
    covered = set(e["intent"] for e in get_training_data())
    assert covered == set(INTENT_CATALOG)


def test_dataset_bilingue():
    langs = set(e["lang"] for e in get_training_data())
    assert "es" in langs and "en" in langs


def test_dataset_formato_correcto():
    for example in get_training_data():
        assert set(example.keys()) == {"text", "intent", "lang"}
        assert example["text"].strip()
        assert example["intent"] in INTENT_CATALOG
        assert example["lang"] in ("es", "en")


def test_dataset_generado_determinista():
    a = generate_training_data(min_examples=1000)
    b = generate_training_data(min_examples=1000)
    assert a == b


def test_stats_dataset():
    stats = training_stats()
    assert stats["total"] >= 1000
    assert stats["intents_covered"] == len(INTENT_CATALOG)
    assert stats["by_lang"]["es"] > 0 and stats["by_lang"]["en"] > 0
