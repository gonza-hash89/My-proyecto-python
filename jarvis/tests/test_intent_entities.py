"""
Tests de brain/intent_entities.py (FASE 3)

Verifica la extracción de entidades por categoría e intención.
"""

from brain.intent_entities import EntityExtractor
from brain.intent_data import INTENT_CATALOG


extractor = EntityExtractor()


def test_genero_musica():
    assert extractor.extract("play_music", "pon música de jazz") == {"genre": "jazz"}


def test_artista_musica():
    r = extractor.extract("play_music", "toca algo de Coldplay")
    assert r.get("artist") == "coldplay"


def test_monto_y_destinatario():
    r = extractor.extract("transfer_money", "envía 100 soles a María")
    assert r.get("amount") == "100"
    assert r.get("recipient") == "maría"


def test_monto_en_dolares():
    r = extractor.extract("transfer_money", "transfer 500 dollars to John")
    assert r.get("amount") == "500"
    assert r.get("recipient") == "john"


def test_habitacion_luces():
    r = extractor.extract("lights_on", "enciende las luces de la sala")
    assert r.get("room") == "sala"


def test_habitacion_en_ingles():
    r = extractor.extract("lights_off", "turn off the lights in the kitchen")
    assert r.get("room") == "kitchen"


def test_duracion_temporizador():
    r = extractor.extract("set_timer", "pon un temporizador de 5 minutos")
    assert r.get("duration") is not None
    assert "5" in r["duration"]


def test_destino_vuelo():
    r = extractor.extract("flight_booking", "reserva un vuelo a Cusco")
    assert r.get("destination") == "cusco"


def test_ciudad_clima():
    r = extractor.extract("weather_query", "cómo está el clima en Lima")
    assert r.get("location") == "lima"


def test_topic_wikipedia():
    r = extractor.extract("search_info", "busca información sobre inteligencia artificial")
    assert r.get("topic") == "inteligencia artificial"


def test_lenguaje_traduccion():
    r = extractor.extract("translate_text", "traduce hola a inglés")
    assert r.get("language") == "inglés"


def test_moneda_crypto():
    r = extractor.extract("crypto_price", "precio de bitcoin")
    assert r.get("coin_name") == "bitcoin"


def test_accion_sistema():
    r = extractor.extract("system_control", "reinicia la computadora")
    assert r.get("action") == "reinicia"


def test_direccion_temperatura():
    r = extractor.extract("adjust_temperature", "quiero más calor")
    assert r.get("direction") == "más calor"


def test_contacto_llamada():
    r = extractor.extract("call_contact", "llama a mamá")
    assert r.get("contact_name") == "mamá"


def test_todos_los_slots_del_catalogo_tienen_handler():
    slots_en_catalogo = set()
    for intent in INTENT_CATALOG.values():
        slots_en_catalogo.update(intent["entities"])
    # Importar la tabla de despacho para verificar cobertura
    from brain.intent_entities import _SLOT_HANDLERS
    sin_handler = slots_en_catalogo - set(_SLOT_HANDLERS)
    assert not sin_handler, f"Slots sin handler: {sin_handler}"
