"""
brain/intent_data.py - Catálogo de intenciones y datos de entrenamiento (SEMANA 4)

Define las 52 intenciones que JARVIS puede reconocer, organizadas en 7 categorías,
con patrones regex y variaciones en español e inglés, más el generador de un
dataset de entrenamiento bilingüe (1000+ ejemplos) para el modelo ML.

Estructura de cada intención:
    {
        "name": str,              # Nombre único de la intención
        "category": str,          # Categoría (basicas, entretenimiento, hogar, finanzas, salud, productividad, viajes)
        "confidence": float,      # Confianza base del patrón (0-1)
        "entities": list[str],    # Slots de entidades que puede extraer
        "patterns_es": list[str], # Regex (sin flags; el matcher usa IGNORECASE)
        "patterns_en": list[str],
        "variations_es": list[str], # Frases literales (ejemplos semilla para el dataset)
        "variations_en": list[str],
    }
"""

from typing import Dict, List, Optional

# ─────────────────────────────────────────────────────────────
# CATEGORÍAS
# ─────────────────────────────────────────────────────────────

CATEGORIES: Dict[str, str] = {
    "basicas": "Básicas",
    "entretenimiento": "Entretenimiento",
    "hogar": "Hogar Inteligente",
    "finanzas": "Finanzas",
    "salud": "Salud y Bienestar",
    "productividad": "Productividad",
    "viajes": "Viajes y Navegación",
}


def _intent(
    name: str,
    category: str,
    confidence: float,
    entities: List[str],
    patterns_es: List[str],
    patterns_en: List[str],
    variations_es: List[str],
    variations_en: List[str],
) -> Dict[str, object]:
    """Construye la estructura estándar de una intención."""
    return {
        "name": name,
        "category": category,
        "confidence": confidence,
        "entities": entities,
        "patterns_es": patterns_es,
        "patterns_en": patterns_en,
        "variations_es": variations_es,
        "variations_en": variations_en,
    }


# ─────────────────────────────────────────────────────────────
# CATÁLOGO DE INTENCIONES (52)
# ─────────────────────────────────────────────────────────────

INTENT_CATALOG: Dict[str, Dict[str, object]] = {}

# ────────── CATEGORÍA 1: BÁSICAS (10) ──────────
INTENT_CATALOG["time_query"] = _intent(
    "time_query", "basicas", 0.99, [],
    [r"\bqu[eé] hora\b", r"la hora", r"dame la hora", r"dime la hora", r"hora actual"],
    [r"\bwhat time\b", r"\btime\b", r"current time", r"tell me the time"],
    ["¿qué hora es?", "dame la hora", "dime la hora", "qué hora es ahora", "hora actual", "dime qué hora es"],
    ["what time is it?", "tell me the time", "current time", "what's the time?"],
)

INTENT_CATALOG["date_query"] = _intent(
    "date_query", "basicas", 0.99, [],
    [r"\bqu[eé] fecha\b", r"\bfecha\b", r"dame la fecha", r"dime la fecha", r"qu[eé] d[ií]a es hoy"],
    [r"\bwhat date\b", r"today's date", r"\bdate\b", r"what day is it"],
    ["¿qué fecha es?", "dame la fecha", "dime la fecha", "qué día es hoy", "qué fecha es hoy"],
    ["what date is it?", "tell me the date", "what day is it today?", "today's date"],
)

INTENT_CATALOG["weather_query"] = _intent(
    "weather_query", "basicas", 0.95, ["location"],
    [r"\bclima\b", r"\btiempo\b", r"est[aá] lloviendo", r"qu[eé] temperatura", r"cu[aá]l.*temperatura",
     r"temperatura (hace|en|de hoy)", r"va a llover", r"pron[oó]stico"],
    [r"\bweather\b", r"is it raining", r"what('s| is) the temperature", r"temperature (in|today|now)",
     r"forecast", r"current temperature"],
    ["¿qué clima hace?", "cómo está el clima", "está lloviendo", "clima de hoy", "qué temperatura hace", "va a llover"],
    ["what's the weather?", "how's the weather", "is it raining?", "weather today", "what's the temperature"],
)

INTENT_CATALOG["help_query"] = _intent(
    "help_query", "basicas", 0.98, [],
    [r"\bayuda\b", r"qu[eé] puedes hacer", r"\bmanual\b", r"c[oó]mo funcionas", r"qu[eé] comandos", r"tus funciones"],
    [r"\bhelp\b", r"what can you do", r"\bmanual\b", r"how do you work", r"your commands"],
    ["ayuda", "qué puedes hacer", "manual de usuario", "cómo funcionas", "qué comandos tienes", "dime tus funciones"],
    ["help", "what can you do?", "manual", "how do you work?", "show me your commands"],
)

INTENT_CATALOG["system_control"] = _intent(
    "system_control", "basicas", 0.99, ["action"],
    [r"apaga.*(computadora|pc|equipo)", r"\breinici[aá]r\b", r"\breinicia\b", r"\bhibernar\b",
     r"bloquea.*(pc|computadora|equipo)", r"pon.*a dormir", r"apaga el equipo"],
    [r"\bshutdown\b", r"\brestart\b", r"\breboot\b", r"sleep mode", r"lock.*(pc|computer)",
     r"turn off.*computer"],
    ["apaga la computadora", "reinicia el sistema", "bloquea la pc", "pon a dormir la computadora", "apaga el equipo", "reinicia la máquina"],
    ["shutdown the computer", "restart the system", "reboot", "lock the pc", "sleep mode", "turn off the computer"],
)

INTENT_CATALOG["news_query"] = _intent(
    "news_query", "basicas", 0.95, ["topic"],
    [r"\bnoticias\b", r"qu[eé] pasa en el mundo", r"\bnews\b", r"[úu]ltimas noticias", r"titulares"],
    [r"\bnews\b", r"what's happening", r"\bheadlines\b", r"latest news"],
    ["cuáles son las noticias", "últimas noticias", "qué pasa en el mundo", "dame los titulares", "noticias de hoy"],
    ["what's the news?", "latest news", "tell me the news", "what's happening in the world", "headlines today"],
)

INTENT_CATALOG["search_info"] = _intent(
    "search_info", "basicas", 0.95, ["topic"],
    [r"busca.*informaci[oó]n", r"\bwikipedia\b", r"qui[eé]n es", r"qu[eé] es", r"busca sobre",
     r"dame datos de", r"investiga\b"],
    [r"search.*(for|about)", r"\bwikipedia\b", r"who is", r"what is", r"look up", r"find out about"],
    ["busca información sobre inteligencia artificial", "busca en wikipedia", "quién es Einstein", "qué es el jazz",
     "dame datos de la historia de Perú", "investiga sobre el clima"],
    ["search for information about programming", "search on wikipedia", "who is Einstein", "what is jazz",
     "look up the history of Peru"],
)

INTENT_CATALOG["reminder_set"] = _intent(
    "reminder_set", "basicas", 0.95, ["time", "task"],
    [r"recu[eé]rdame", r"\brecordatorio\b", r"alarma para", r"que no se me olvide", r"recu[eé]rdame en"],
    [r"remind me", r"\breminder\b", r"set.*alarm", r"don't let me forget"],
    ["recuérdame comprar leche", "pon un recordatorio para llamar al médico", "alarma para las 8 de la mañana",
     "recuérdame en 10 minutos", "que no se me olvide pagar internet"],
    ["remind me to buy milk", "set a reminder", "set an alarm for tomorrow", "remind me in 10 minutes",
     "don't let me forget to call the doctor"],
)

INTENT_CATALOG["change_name"] = _intent(
    "change_name", "basicas", 0.95, ["new_name"],
    [r"cambia tu nombre", r"ll[aá]mame", r"te llamar[eéaá]", r"c[oó]mo te llamas", r"nuevo nombre", r"quiero llamarte", r"tu nombre"],
    [r"change your name", r"what's your name", r"call you\b", r"your (new )?name"],
    ["cambia tu nombre a Jarvis", "quiero llamarte Jarvis", "te llamarás Jarvis", "cómo te llamas", "dame tu nombre"],
    ["change your name", "what's your name?", "I want to call you Jarvis", "your new name"],
)

INTENT_CATALOG["exit"] = _intent(
    "exit", "basicas", 0.99, [],
    [r"\bsalir\b", r"descon[eé]ctate", r"adi[oó]s", r"\bbye\b", r"ya no te necesito", r"ap[aá]gate", r"\bhasta luego"],
    [r"\bexit\b", r"\bgoodbye\b", r"\bbye\b", r"shut down", r"that's all", r"go to sleep", r"good night"],
    ["salir", "desconéctate", "adiós jarvis", "bye", "ya no te necesito", "hasta luego", "apágate"],
    ["exit", "goodbye jarvis", "bye", "shut down", "that's all for now", "good night"],
)

# ────────── CATEGORÍA 2: ENTRETENIMIENTO (10) ──────────
INTENT_CATALOG["play_music"] = _intent(
    "play_music", "entretenimiento", 0.98, ["genre", "artist", "song_name"],
    [r"reproduce.*m[uú]sica", r"pon.*(canci[oó]n|m[uú]sica)", r"\bm[uú]sica\b", r"toca (algo|m[uú]sica)",
     r"quiero escuchar", r"pon una canci[oó]n", r"\bplaylist\b"],
    [r"play.*music", r"put.*song", r"\bmusic\b", r"\bsong\b", r"playlist", r"play some",
     r"want to listen to", r"play (coldplay|bad bunny|shakira|the beatles)"],
    ["reproducir música", "pon música de rock", "pon una canción", "quiero escuchar jazz", "toca algo de Coldplay"],
    ["play music", "put on a song", "play some jazz", "I want to listen to rock", "play Coldplay"],
)

INTENT_CATALOG["play_podcast"] = _intent(
    "play_podcast", "entretenimiento", 0.95, ["podcast_name"],
    [r"\bpodcast\b", r"escucha.*podcast", r"pon.*podcast"],
    [r"\bpodcast\b", r"listen.*podcast", r"play.*podcast"],
    ["reproducir podcast", "pon el podcast de tecnología", "escucha un podcast de ciencia", "podcast de historia"],
    ["play a podcast", "play the technology podcast", "listen to a podcast"],
)

INTENT_CATALOG["play_audiobook"] = _intent(
    "play_audiobook", "entretenimiento", 0.95, ["book_title"],
    [r"audiolibro", r"libro.*audio", r"escucha.*libro"],
    [r"audiobook", r"audio book", r"listen.*book"],
    ["pon un audiolibro", "escucha el audiolibro de Cien años de soledad", "audiolibro de ciencia ficción"],
    ["play an audiobook", "listen to the audiobook", "audio book"],
)

INTENT_CATALOG["watch_videos"] = _intent(
    "watch_videos", "entretenimiento", 0.98, ["topic"],
    [r"\byoutube\b", r"ver videos", r"\bv[ií]deos\b", r"reproduce.*video", r"mira.*video"],
    [r"\byoutube\b", r"watch videos", r"\bvideos\b", r"play.*video"],
    ["abre youtube", "quiero ver videos", "pon videos de programación", "abrir youtube"],
    ["open youtube", "watch videos", "play some videos", "youtube"],
)

INTENT_CATALOG["watch_streaming"] = _intent(
    "watch_streaming", "entretenimiento", 0.95, ["platform", "title"],
    [r"\bnetflix\b", r"amazon prime", r"\bdisney\b", r"\bhbo\b", r"ver pel[ií]cula", r"\bpel[ií]cula\b",
     r"\bstreaming\b", r"\bserie\b"],
    [r"\bnetflix\b", r"prime video", r"\bdisney\b", r"\bmovie\b", r"\bstreaming\b", r"\bseries\b"],
    ["abre netflix", "ver una película", "pon una serie", "amazon prime", "quiero ver una película de acción"],
    ["open netflix", "watch a movie", "put on a series", "prime video", "I want to watch a movie"],
)

INTENT_CATALOG["tell_joke"] = _intent(
    "tell_joke", "entretenimiento", 0.98, ["topic"],
    [r"cu[eé]ntame un chiste", r"\bchiste\b", r"hazme re[ií]r", r"dime un chiste", r"una broma"],
    [r"\bjoke\b", r"make me laugh", r"tell me a joke"],
    ["cuéntame un chiste", "dime un chiste", "hazme reír", "necesito un chiste", "cuenta una broma"],
    ["tell me a joke", "make me laugh", "tell a joke", "I need a joke"],
)

INTENT_CATALOG["play_games"] = _intent(
    "play_games", "entretenimiento", 0.95, ["game_name"],
    [r"\bjugar\b", r"\bjuego\b", r"videojuego", r"\bjuega\b", r"quiero jugar"],
    [r"play games", r"video game", r"\bgaming\b", r"let's play", r"want to play"],
    ["jugar un juego", "quiero jugar", "pon un videojuego", "juega algo conmigo"],
    ["play games", "I want to play", "let's play a game", "video game"],
)

INTENT_CATALOG["take_screenshot"] = _intent(
    "take_screenshot", "entretenimiento", 0.97, ["format", "location"],
    [r"captura.*pantalla", r"\bscreenshot\b", r"(toma|saca).*foto de pantalla", r"\bcaptura\b"],
    [r"\bscreenshot\b", r"take a screenshot", r"capture.*screen"],
    ["captura de pantalla", "toma una captura", "haz un screenshot", "saca una foto de pantalla"],
    ["screenshot", "take a screenshot", "capture the screen"],
)

INTENT_CATALOG["record_video"] = _intent(
    "record_video", "entretenimiento", 0.95, ["format"],
    [r"grabar.*video", r"grab(ar|a).*pantalla", r"grabaci[oó]n", r"empieza a grabar"],
    [r"record.*video", r"record.*screen", r"screen recording", r"start recording"],
    ["grabar un video", "graba la pantalla", "empieza a grabar", "grabación de pantalla"],
    ["record a video", "record the screen", "start recording", "screen recording"],
)

INTENT_CATALOG["translate_text"] = _intent(
    "translate_text", "entretenimiento", 0.95, ["text", "language"],
    [r"\btraduce\b", r"traducci[oó]n", r"\btraducir\b", r"\btraductor\b"],
    [r"\btranslate\b", r"\btranslation\b", r"\btranslator\b"],
    ["traduce hola a inglés", "traducción de esta frase", "traduce al francés", "ponme el traductor"],
    ["translate hello to spanish", "translation of this sentence", "translate to french", "translator"],
)

# ────────── CATEGORÍA 3: HOGAR INTELIGENTE (8) ──────────
INTENT_CATALOG["lights_on"] = _intent(
    "lights_on", "hogar", 0.98, ["room"],
    [r"enciende.*luz", r"prende.*luz", r"\bluces\b", r"iluminaci[oó]n", r"encender.*luz"],
    [r"turn on.*light", r"\blights\b", r"turn.*light on", r"turn.*lights on"],
    ["enciende las luces", "prende la luz de la sala", "enciende las luces de la cocina", "iluminación"],
    ["turn on the lights", "turn on the living room lights", "turn the lights on", "lights"],
)

INTENT_CATALOG["lights_off"] = _intent(
    "lights_off", "hogar", 0.98, ["room"],
    [r"apaga.*(luces|luz)", r"luces.*apagadas", r"\boscuro\b"],
    [r"turn off.*light", r"lights off\b", r"turn.*lights off"],
    ["apaga las luces", "apaga la luz del dormitorio", "apaga todas las luces", "deja todo oscuro"],
    ["turn off the lights", "turn the lights off", "lights off"],
)

INTENT_CATALOG["adjust_temperature"] = _intent(
    "adjust_temperature", "hogar", 0.95, ["degrees", "direction"],
    [r"(ajusta|ajustar|pon|poner|sube|subir|baja|bajar|cambia|cambiar).*(temperatura|termo)",
     r"temperatura.*grados", r"m[aá]s (calor|fr[ií]o)", r"menos (calor|fr[ií]o)", r"\bgrados\b",
     r"\btermostato\b", r"calefacci[oó]n", r"aire acondicionado"],
    [r"(adjust|set|turn up|turn down|change|raise|lower).*(temperature|thermo)",
     r"temperature.*degrees", r"\bwarmer\b", r"\bcooler\b", r"\bhotter\b", r"\bcolder\b",
     r"\bdegrees\b", r"\bthermostat\b", r"\bheating\b", r"\bheat\b", r"air conditioning"],
    ["ajusta la temperatura a 20 grados", "sube la temperatura", "más calor", "menos frío", "baja el termostato", "pon el aire acondicionado"],
    ["adjust the temperature to 20 degrees", "make it warmer", "turn up the heat", "set the thermostat to 20"],
)

INTENT_CATALOG["lock_door"] = _intent(
    "lock_door", "hogar", 0.98, ["door_name"],
    [r"cierra.*puerta", r"bloquea.*puerta", r"traba.*puerta", r"cierra con llave"],
    [r"\block\b.*door", r"close.*door", r"\block it up\b"],
    ["cierra la puerta", "bloquea la puerta principal", "traba la puerta", "cierra con llave"],
    ["lock the door", "close the door", "lock the front door"],
)

INTENT_CATALOG["unlock_door"] = _intent(
    "unlock_door", "hogar", 0.98, ["door_name"],
    [r"abre.*puerta", r"desbloquea.*puerta", r"destraba.*puerta"],
    [r"unlock.*door", r"open.*door", r"unlock it"],
    ["abre la puerta", "desbloquea la puerta principal", "abre la puerta de la cochera"],
    ["unlock the door", "open the door", "unlock the front door"],
)

INTENT_CATALOG["close_curtains"] = _intent(
    "close_curtains", "hogar", 0.95, ["room"],
    [r"cierra.*cortinas", r"corre.*cortinas", r"cortinas.*cerradas"],
    [r"close.*curtains", r"close.*blinds"],
    ["cierra las cortinas", "corre las cortinas de la sala", "cierra las cortinas del dormitorio"],
    ["close the curtains", "close the blinds", "close the curtains in the living room"],
)

INTENT_CATALOG["open_curtains"] = _intent(
    "open_curtains", "hogar", 0.95, ["room"],
    [r"abre.*cortinas", r"cortinas.*abiertas"],
    [r"open.*curtains", r"open.*blinds"],
    ["abre las cortinas", "abre las cortinas del dormitorio"],
    ["open the curtains", "open the blinds", "open the curtains in the living room"],
)

INTENT_CATALOG["arm_security"] = _intent(
    "arm_security", "hogar", 0.98, [],
    [r"activa.*seguridad", r"(alarma de seguridad|sistema de alarma)", r"\bvigilancia\b", r"seguridad.*activada", r"c[áa]maras"],
    [r"arm.*security", r"security system", r"\bsurveillance\b", r"turn on the alarm", r"activate the alarm"],
    ["activa la seguridad", "activa el sistema de alarma", "enciende la vigilancia", "activa las cámaras"],
    ["arm the security", "turn on the alarm", "activate the security system", "surveillance on"],
)

# ────────── CATEGORÍA 4: FINANZAS (7) ──────────
INTENT_CATALOG["check_balance"] = _intent(
    "check_balance", "finanzas", 0.95, ["account_type"],
    [r"\bsaldo\b", r"dinero.*cuenta", r"cu[aá]nto dinero tengo", r"\bbalance\b"],
    [r"\bbalance\b", r"money in.*account", r"how much money", r"account balance"],
    ["cuál es mi saldo", "cuánto dinero tengo en mi cuenta", "cuál es mi balance", "saldo de mi cuenta"],
    ["what's my balance?", "how much money do I have", "check my account balance", "my balance"],
)

INTENT_CATALOG["transfer_money"] = _intent(
    "transfer_money", "finanzas", 0.90, ["amount", "recipient"],
    [r"transferir.*dinero", r"enviar.*dinero", r"\btransferencia\b", r"mandar.*dinero", r"transfiere",
     r"env[ií]a", r"manda", r"env[ií]a.*\d+"],
    [r"transfer money", r"send money", r"\btransfer\b", r"send \d+.*(dollars|to)"],
    ["transferir dinero a Juan", "envía 100 soles a María", "haz una transferencia", "manda dinero a Pedro"],
    ["transfer money to John", "send 100 dollars to Mary", "make a transfer"],
)

INTENT_CATALOG["pay_bills"] = _intent(
    "pay_bills", "finanzas", 0.95, ["bill_type"],
    [r"pagar.*factura", r"(pago|pagar|paga).*servicios", r"pagar.*cuentas", r"\bfacturas\b", r"(pagar|paga).*recibos?"],
    [r"pay.*bill", r"pay.*utilities", r"\bbill\b"],
    ["pagar las facturas", "pagar los servicios", "paga el recibo de luz", "pagar mis cuentas"],
    ["pay the bills", "pay my utilities", "pay the electricity bill"],
)

INTENT_CATALOG["check_investments"] = _intent(
    "check_investments", "finanzas", 0.90, ["investment_type"],
    [r"\binversiones\b", r"\bportafolio\b", r"\bacciones\b", r"\binvertir\b", r"rendimiento.*inversi[oó]n"],
    [r"\binvestments\b", r"\bportfolio\b", r"\bstocks\b"],
    ["cómo van mis inversiones", "revisa mi portafolio", "cuánto tengo en acciones", "rendimiento de mis inversiones"],
    ["how are my investments", "check my portfolio", "how much do I have in stocks"],
)

INTENT_CATALOG["get_exchange_rate"] = _intent(
    "get_exchange_rate", "finanzas", 0.90, ["currency_from", "currency_to"],
    [r"tipo de cambio", r"d[oó]lar.*sol", r"conversi[oó]n", r"cu[aá]nto vale el d[oó]lar", r"cambio de moneda"],
    [r"exchange rate", r"dollar.*(to|peso)", r"currency conversion", r"\bconversion\b"],
    ["cuál es el tipo de cambio", "cuánto vale el dólar en soles", "conversión de dólares a euros", "tipo de cambio de hoy"],
    ["what's the exchange rate", "how much is the dollar to peso", "currency conversion"],
)

INTENT_CATALOG["budget_report"] = _intent(
    "budget_report", "finanzas", 0.90, ["period"],
    [r"\bpresupuesto\b", r"gastos.*mes", r"reporte.*gastos", r"qu[eé] he gastado", r"\bgastos\b"],
    [r"\bbudget\b", r"monthly expenses", r"expense report", r"\bspending\b", r"\bexpenses\b"],
    ["muéstrame el presupuesto", "cuáles fueron mis gastos del mes", "reporte de gastos", "en qué he gastado"],
    ["show me my budget", "what were my expenses this month", "spending report"],
)

INTENT_CATALOG["crypto_price"] = _intent(
    "crypto_price", "finanzas", 0.90, ["coin_name"],
    [r"\bbitcoin\b", r"criptomoneda", r"\bcrypto\b", r"precio.*bitcoin", r"\bethereum\b"],
    [r"\bbitcoin\b", r"cryptocurrency", r"\bcrypto\b", r"\bethereum\b"],
    ["precio de bitcoin", "cuánto vale bitcoin", "precio de las criptomonedas", "cuánto cuesta ethereum"],
    ["bitcoin price", "how much is bitcoin", "cryptocurrency prices", "ethereum price"],
)

# ────────── CATEGORÍA 5: SALUD Y BIENESTAR (5) ──────────
INTENT_CATALOG["fitness_tracking"] = _intent(
    "fitness_tracking", "salud", 0.95, ["metric"],
    [r"calor[ií]as", r"\bpasos\b", r"\bentrenamiento\b", r"\bejercicio\b", r"\brutina\b"],
    [r"\bcalories\b", r"\bsteps\b", r"\bworkout\b", r"\bexercise\b"],
    ["cuántas calorías quemé", "cuántos pasos di", "muéstrame mi entrenamiento", "rutina de ejercicio"],
    ["how many calories did I burn", "how many steps today", "show my workout", "exercise routine"],
)

INTENT_CATALOG["sleep_tracking"] = _intent(
    "sleep_tracking", "salud", 0.95, ["metric"],
    [r"horas de sue[ñn]o", r"\bsue[ñn]o\b", r"calidad del sue[ñn]o", r"descanso", r"horas dorm[ií]"],
    [r"\bsleep\b", r"hours slept", r"sleep quality", r"\brest\b"],
    ["cuántas horas dormí", "calidad de mi sueño", "mis horas de sueño", "cómo fue mi descanso"],
    ["how many hours did I sleep", "my sleep quality", "sleep tracking"],
)

INTENT_CATALOG["water_reminder"] = _intent(
    "water_reminder", "salud", 0.98, [],
    [r"toma agua", r"recordatorio de agua", r"hidrataci[oó]n", r"tomar agua", r"hidrat[ae]"],
    [r"drink water", r"water reminder", r"\bhydration\b", r"\bhydrated\b"],
    ["recuérdame tomar agua", "pon un recordatorio de agua", "dime que me hidrate", "tomar agua cada hora"],
    ["remind me to drink water", "water reminder", "keep me hydrated"],
)

INTENT_CATALOG["meditation"] = _intent(
    "meditation", "salud", 0.98, ["duration"],
    [r"meditaci[oó]n", r"\brelajarse\b", r"\brelajar\b", r"\bzen\b", r"\bmeditar\b", r"respiraci[oó]n"],
    [r"\bmeditation\b", r"\brelax\b", r"\bzen\b", r"\bmeditate\b", r"breathing exercise"],
    ["guíame en una meditación", "quiero meditar 10 minutos", "hazme relajar", "ejercicio de respiración"],
    ["guide me in meditation", "I want to meditate for 10 minutes", "help me relax", "breathing exercise"],
)

INTENT_CATALOG["health_stats"] = _intent(
    "health_stats", "salud", 0.90, ["stat_type"],
    [r"presi[oó]n arterial", r"frecuencia card[ií]aca", r"\bsalud\b", r"\bpulso\b", r"ritmo card[ií]aco"],
    [r"blood pressure", r"heart rate", r"\bhealth\b", r"\bpulse\b"],
    ["cuál es mi presión arterial", "mi frecuencia cardíaca", "revisa mis signos de salud", "cuál es mi pulso"],
    ["what's my blood pressure", "my heart rate", "check my health stats", "my pulse"],
)

# ────────── CATEGORÍA 6: PRODUCTIVIDAD (7) ──────────
INTENT_CATALOG["open_application"] = _intent(
    "open_application", "productividad", 0.95, ["app_name"],
    [r"abre google", r"abre gmail", r"\baplicaci[oó]n\b", r"abre chrome", r"abre excel", r"abre word",
     r"abre visual studio", r"abre spotify", r"abre youtube", r"lanza"],
    [r"open google", r"open gmail", r"open chrome", r"open excel", r"open word", r"\bapplication\b",
     r"\blaunch\b", r"open spotify"],
    ["abre google", "abre gmail", "abre chrome", "abre excel", "abre word", "abre visual studio", "abre spotify"],
    ["open google", "open gmail", "open chrome", "open excel", "open word", "launch the app"],
)

INTENT_CATALOG["send_email"] = _intent(
    "send_email", "productividad", 0.90, ["recipient", "subject"],
    [r"enviar.*(email|correo)", r"\bmail a\b", r"correo a", r"manda.*correo", r"env[ií]a.*(correo|email|mail)"],
    [r"send.*email", r"email.*to", r"mail to", r"message to"],
    ["envía un email a Juan", "enviar correo a María", "manda un mail a Pedro", "correo a mi jefe"],
    ["send an email to John", "email to Mary", "mail to my boss"],
)

INTENT_CATALOG["calendar_event"] = _intent(
    "calendar_event", "productividad", 0.90, ["date"],
    [r"\bcalendario\b", r"pr[oó]ximos eventos", r"\breuni[oó]nes?\b", r"\bagenda\b", r"qu[eé] tengo"],
    [r"\bcalendar\b", r"upcoming events", r"\bmeetings?\b", r"\bagenda\b", r"\bschedule\b"],
    ["muéstrame mi calendario", "qué reuniones tengo", "próximos eventos", "qué tengo agendado"],
    ["show me my calendar", "what meetings do I have", "upcoming events", "my schedule"],
)

INTENT_CATALOG["take_notes"] = _intent(
    "take_notes", "productividad", 0.90, ["content"],
    [r"\banota\b", r"\bnotas\b", r"\bapunta\b", r"guarda una nota", r"escribe una nota", r"\brecordar\b", r"\brecuerda\b"],
    [r"take notes", r"\bnotes\b", r"write.*note", r"make a note", r"\bremember\b"],
    ["anota comprar leche", "guarda una nota", "apunta la idea", "escribe una nota sobre el proyecto", "recuerda esto"],
    ["take notes", "write a note", "make a note about the project", "remember this"],
)

INTENT_CATALOG["create_task"] = _intent(
    "create_task", "productividad", 0.90, ["task_description"],
    [r"\btarea\b", r"crear lista", r"\bto-do\b", r"agrega una tarea", r"\bpendiente\b"],
    [r"\btask\b", r"create list", r"to-do", r"add.*task"],
    ["crea una tarea", "agrega una tarea a mi lista", "anota en mi to-do", "tengo una tarea pendiente"],
    ["create a task", "add a task to my list", "add to my to-do"],
)

INTENT_CATALOG["set_timer"] = _intent(
    "set_timer", "productividad", 0.95, ["duration"],
    [r"\btemporizador\b", r"\btimer\b", r"alarma (para|en).*(minuto|hora)", r"cron[oó]metro", r"pon.*temporizador"],
    [r"\btimer\b", r"alarm.*(minute|hour|second)", r"\bcountdown\b", r"set.*timer"],
    ["pon un temporizador de 5 minutos", "alarma para 10 minutos", "activa el cronómetro", "temporizador de una hora"],
    ["set a timer for 5 minutes", "set an alarm for 10 minutes", "countdown timer", "start a timer"],
)

INTENT_CATALOG["call_contact"] = _intent(
    "call_contact", "productividad", 0.95, ["contact_name"],
    [r"llama a", r"\bllamada\b", r"\bcontacto\b", r"ll[aá]male", r"marca a"],
    [r"\bcall\b", r"phone call", r"\bcontact\b", r"call up"],
    ["llama a Juan", "haz una llamada", "llámale a mamá", "marca a Pedro"],
    ["call John", "make a call", "call my mom", "phone call"],
)

# ────────── CATEGORÍA 7: VIAJES Y NAVEGACIÓN (5) ──────────
INTENT_CATALOG["directions"] = _intent(
    "directions", "viajes", 0.95, ["destination"],
    [r"direcciones a", r"c[oó]mo llego", r"\bruta\b", r"navega a", r"c[oó]mo llego a", r"qu[eé] camino"],
    [r"\bdirections\b", r"how do i get", r"\broute\b", r"\bnavigate\b"],
    ["direcciones a Cusco", "cómo llego a Lima", "traza una ruta", "navega a la playa"],
    ["directions to Lima", "how do I get to the airport", "route to downtown", "navigate home"],
)

INTENT_CATALOG["traffic_info"] = _intent(
    "traffic_info", "viajes", 0.90, ["location"],
    [r"\btr[aá]fico\b", r"congesti[oó]n", r"\bcarreteras\b", r"hay tr[aá]fico"],
    [r"\btraffic\b", r"\bcongestion\b", r"\broads\b"],
    ["cómo está el tráfico", "hay tráfico en Lima", "congestión en las carreteras", "estado del tráfico"],
    ["how's the traffic", "is there traffic", "traffic conditions", "road congestion"],
)

INTENT_CATALOG["book_ride"] = _intent(
    "book_ride", "viajes", 0.95, ["destination"],
    [r"pedir taxi", r"\buber\b", r"\btransporte\b", r"pide un taxi", r"\btaxi\b"],
    [r"call .*taxi", r"\buber\b", r"transportation", r"book a ride"],
    ["pedir un taxi", "pide un uber", "llama un taxi a mi casa", "necesito transporte"],
    ["call a taxi", "order an uber", "book a ride"],
)

INTENT_CATALOG["flight_booking"] = _intent(
    "flight_booking", "viajes", 0.90, ["destination", "date"],
    [r"\bvuelo\b", r"reserva.*vuelo", r"boleto a[eé]reo", r"vuelos a"],
    [r"\bflights?\b", r"book flight", r"airline ticket"],
    ["reserva un vuelo a Cusco", "busca vuelos a Lima", "boleto aéreo a Madrid", "cuánto cuesta un vuelo"],
    ["book a flight to Lima", "find flights to Madrid", "airline ticket"],
)

INTENT_CATALOG["hotel_booking"] = _intent(
    "hotel_booking", "viajes", 0.90, ["destination", "date"],
    [r"\bhoteles?\b", r"reserva.*hotel", r"\bhospedaje\b", r"\bhospedarme\b", r"\balojamiento\b"],
    [r"\bhotels?\b", r"book hotel", r"\baccommodation\b", r"where can i stay"],
    ["reserva un hotel en Cusco", "busca hoteles en Lima", "dónde puedo hospedarme", "alojamiento en Arequipa"],
    ["book a hotel in Lima", "find hotels in Madrid", "where can I stay"],
)


# ─────────────────────────────────────────────────────────────
# FILLERS: valores para generar variaciones del dataset
# ─────────────────────────────────────────────────────────────

FILLERS: Dict[str, List[str]] = {
    "topic": ["programación", "historia", "ciencia", "deportes", "música", "inteligencia artificial", "cocina", "viajes"],
    "topic_en": ["programming", "history", "science", "sports", "music", "artificial intelligence", "cooking"],
    "person": ["Albert Einstein", "Shakira", "Messi", "Marie Curie", "Steve Jobs"],
    "person_en": ["Albert Einstein", "Shakira", "Messi", "Marie Curie", "Steve Jobs"],
    "genre": ["rock", "pop", "jazz", "clásica", "electrónica", "salsa", "reggaetón", "cumbia"],
    "genre_en": ["rock", "pop", "jazz", "classical", "electronic", "reggaeton"],
    "artist": ["Coldplay", "Bad Bunny", "Shakira", "The Beatles"],
    "artist_en": ["Coldplay", "Bad Bunny", "Shakira", "The Beatles"],
    "song": ["Blinding Lights", "Despacito", "Shape of You"],
    "song_en": ["Blinding Lights", "Despacito", "Shape of You"],
    "app": ["Google", "Chrome", "Excel", "Word", "Spotify", "Visual Studio", "Gmail"],
    "app_en": ["Google", "Chrome", "Excel", "Word", "Spotify", "Gmail"],
    "room": ["la sala", "la cocina", "el dormitorio", "el baño"],
    "room_en": ["the living room", "the kitchen", "the bedroom", "the bathroom"],
    "amount": ["50", "100", "200", "500"],
    "amount_en": ["50", "100", "200", "500"],
    "currency": ["soles", "dólares", "euros"],
    "currency_en": ["dollars", "euros", "soles"],
    "recipient": ["Juan", "María", "Pedro", "Lucía"],
    "recipient_en": ["John", "Mary", "Peter", "Lucy"],
    "contact": ["Juan", "mamá", "papá", "María"],
    "contact_en": ["John", "mom", "dad", "Mary"],
    "duration": ["5 minutos", "10 minutos", "15 minutos", "30 minutos", "una hora"],
    "duration_en": ["5 minutes", "10 minutes", "30 minutes", "an hour"],
    "city": ["Lima", "Cusco", "Arequipa", "Trujillo", "Madrid"],
    "city_en": ["Lima", "Madrid", "New York", "Bogotá", "Mexico City"],
    "task": ["comprar leche", "llamar al médico", "pagar internet", "hacer ejercicio"],
    "task_en": ["buy milk", "call the doctor", "pay the internet", "exercise"],
    "bill": ["internet", "luz", "agua", "teléfono"],
    "bill_en": ["internet", "electricity", "water", "phone"],
    "podcast": ["de tecnología", "de ciencia", "de historia", "de negocios"],
    "podcast_en": ["about technology", "about science", "about history"],
    "book": ["Cien años de soledad", "El principito", "Don Quijote"],
    "book_en": ["One Hundred Years of Solitude", "The Little Prince", "Don Quixote"],
    "news_topic": ["tecnología", "política", "deportes", "economía", "ciencia"],
    "news_topic_en": ["technology", "politics", "sports", "economy", "science"],
    "language": ["inglés", "francés", "portugués", "alemán"],
    "language_en": ["English", "French", "Spanish", "German"],
    "phrase": ["hola mundo", "buenos días", "te quiero"],
    "phrase_en": ["hello world", "good morning", "I love you"],
    "video_topic": ["programación", "recetas", "noticias", "tutoriales"],
    "video_topic_en": ["programming", "recipes", "news", "tutorials"],
    "movie": ["acción", "comedia", "terror", "ciencia ficción"],
    "movie_en": ["action", "comedy", "horror", "sci-fi"],
    "temperature": ["20", "22", "25", "18"],
    "direction_es": ["más calor", "más frío", "menos calor", "menos frío"],
    "direction_en": ["warmer", "cooler", "hotter", "colder"],
    "door": ["la puerta principal", "la puerta de la cochera", "el portón", "la puerta trasera"],
    "door_en": ["the front door", "the garage door", "the gate", "the back door"],
    "location": ["la pantalla completa", "la ventana activa", "el escritorio", "una parte de la pantalla"],
    "location_en": ["the full screen", "the active window", "the desktop", "part of the screen"],
    "game": ["ajedrez", "sudoku", "adivinanzas", "un juego de mesa"],
    "game_en": ["chess", "sudoku", "a quiz", "a board game"],
    "investment_type": ["acciones", "fondos mutuos", "mi portafolio", "criptomonedas"],
    "investment_type_en": ["stocks", "mutual funds", "my portfolio", "crypto"],
    "period": ["este mes", "enero", "este año", "el último trimestre"],
    "period_en": ["this month", "january", "this year", "this quarter"],
    "coin": ["bitcoin", "ethereum", "dogecoin", "cardano"],
    "coin_en": ["bitcoin", "ethereum", "dogecoin", "cardano"],
    "sleep_metric": ["anoche", "esta noche", "esta semana", "el fin de semana"],
    "sleep_metric_en": ["last night", "tonight", "this week", "last weekend"],
    "stat_type": ["presión arterial", "frecuencia cardíaca", "pulso", "ritmo cardíaco"],
    "stat_type_en": ["blood pressure", "heart rate", "pulse"],
    "new_name": ["Jarvis", "Alex", "JARVIS"],
    "new_name_en": ["Jarvis", "Alex", "JARVIS"],
}


# ─────────────────────────────────────────────────────────────
# TEMPLATES: plantillas para expandir el dataset de entrenamiento
# Formato: (plantilla_con_slots, "es"|"en", [slot1, slot2, ...])
# ─────────────────────────────────────────────────────────────

TEMPLATES: Dict[str, List[tuple]] = {
    "weather_query": [
        ("cómo está el clima en {city}", "es", ["city"]),
        ("cuál es la temperatura en {city}", "es", ["city"]),
        ("how's the weather in {city_en}", "en", ["city_en"]),
        ("what's the temperature in {city_en}", "en", ["city_en"]),
    ],
    "search_info": [
        ("busca información sobre {topic}", "es", ["topic"]),
        ("busca en wikipedia {topic}", "es", ["topic"]),
        ("dame datos de {topic}", "es", ["topic"]),
        ("quién es {person}", "es", ["person"]),
        ("search for information about {topic_en}", "en", ["topic_en"]),
        ("look up {topic_en} on wikipedia", "en", ["topic_en"]),
        ("who is {person_en}", "en", ["person_en"]),
    ],
    "reminder_set": [
        ("recuérdame {task}", "es", ["task"]),
        ("alarma para {task}", "es", ["task"]),
        ("recordatorio para {task}", "es", ["task"]),
        ("remind me to {task_en}", "en", ["task_en"]),
        ("set a reminder to {task_en}", "en", ["task_en"]),
    ],
    "news_query": [
        ("noticias de {news_topic}", "es", ["news_topic"]),
        ("dame noticias de {news_topic}", "es", ["news_topic"]),
        ("news about {news_topic_en}", "en", ["news_topic_en"]),
        ("tell me the {news_topic_en} news", "en", ["news_topic_en"]),
    ],
    "play_music": [
        ("pon música de {genre}", "es", ["genre"]),
        ("reproduce {genre}", "es", ["genre"]),
        ("toca algo de {artist}", "es", ["artist"]),
        ("pon {song} de {artist}", "es", ["song", "artist"]),
        ("play some {genre_en}", "en", ["genre_en"]),
        ("play {artist_en}", "en", ["artist_en"]),
        ("put on {song_en} by {artist_en}", "en", ["song_en", "artist_en"]),
    ],
    "play_podcast": [
        ("pon el podcast {podcast}", "es", ["podcast"]),
        ("escucha el podcast {podcast}", "es", ["podcast"]),
        ("play the podcast {podcast_en}", "en", ["podcast_en"]),
    ],
    "play_audiobook": [
        ("pon el audiolibro de {book}", "es", ["book"]),
        ("audiolibro de {book}", "es", ["book"]),
        ("play the audiobook {book_en}", "en", ["book_en"]),
    ],
    "watch_videos": [
        ("pon videos de {video_topic}", "es", ["video_topic"]),
        ("ver videos de {video_topic}", "es", ["video_topic"]),
        ("play videos about {video_topic_en}", "en", ["video_topic_en"]),
        ("watch {video_topic_en} videos", "en", ["video_topic_en"]),
    ],
    "watch_streaming": [
        ("ver una película de {movie}", "es", ["movie"]),
        ("pon una película de {movie}", "es", ["movie"]),
        ("watch a {movie_en} movie", "en", ["movie_en"]),
        ("put on a {movie_en} movie", "en", ["movie_en"]),
    ],
    "tell_joke": [
        ("cuéntame un chiste de {topic}", "es", ["topic"]),
        ("dime un chiste de {topic}", "es", ["topic"]),
        ("tell me a joke about {topic_en}", "en", ["topic_en"]),
    ],
    "open_application": [
        ("abre {app}", "es", ["app"]),
        ("abrir {app}", "es", ["app"]),
        ("open {app_en}", "en", ["app_en"]),
        ("launch {app_en}", "en", ["app_en"]),
    ],
    "send_email": [
        ("envía un correo a {recipient}", "es", ["recipient"]),
        ("manda un mail a {recipient}", "es", ["recipient"]),
        ("send an email to {recipient_en}", "en", ["recipient_en"]),
        ("email {recipient_en}", "en", ["recipient_en"]),
    ],
    "take_notes": [
        ("anota {task}", "es", ["task"]),
        ("guarda una nota sobre {topic}", "es", ["topic"]),
        ("write a note about {topic_en}", "en", ["topic_en"]),
        ("make a note to {task_en}", "en", ["task_en"]),
    ],
    "create_task": [
        ("agrega la tarea {task}", "es", ["task"]),
        ("crea una tarea para {task}", "es", ["task"]),
        ("add the task {task_en}", "en", ["task_en"]),
        ("create a task to {task_en}", "en", ["task_en"]),
    ],
    "set_timer": [
        ("temporizador de {duration}", "es", ["duration"]),
        ("pon una alarma en {duration}", "es", ["duration"]),
        ("set a timer for {duration_en}", "en", ["duration_en"]),
        ("alarm in {duration_en}", "en", ["duration_en"]),
    ],
    "call_contact": [
        ("llama a {contact}", "es", ["contact"]),
        ("marca a {contact}", "es", ["contact"]),
        ("call {contact_en}", "en", ["contact_en"]),
        ("phone {contact_en}", "en", ["contact_en"]),
    ],
    "lights_on": [
        ("enciende las luces de {room}", "es", ["room"]),
        ("prende la luz de {room}", "es", ["room"]),
        ("turn on the lights in {room_en}", "en", ["room_en"]),
        ("turn the {room_en} lights on", "en", ["room_en"]),
    ],
    "lights_off": [
        ("apaga las luces de {room}", "es", ["room"]),
        ("apaga la luz de {room}", "es", ["room"]),
        ("turn off the lights in {room_en}", "en", ["room_en"]),
        ("turn the {room_en} lights off", "en", ["room_en"]),
    ],
    "adjust_temperature": [
        ("pon la temperatura en {temperature} grados", "es", ["temperature"]),
        ("baja la temperatura a {temperature}", "es", ["temperature"]),
        ("quiero {direction_es}", "es", ["direction_es"]),
        ("set the temperature to {temperature} degrees", "en", ["temperature"]),
        ("make it {direction_en}", "en", ["direction_en"]),
    ],
    "arm_security": [
        ("activa la alarma", "es", []),
        ("activa las cámaras de seguridad", "es", []),
        ("activate the alarm", "en", []),
        ("turn on the security cameras", "en", []),
    ],
    "check_balance": [
        ("saldo de mi cuenta", "es", []),
        ("cuánto tengo en mi cuenta", "es", []),
        ("check my account balance", "en", []),
        ("how much do I have", "en", []),
    ],
    "transfer_money": [
        ("transfiere {amount} soles a {recipient}", "es", ["amount", "recipient"]),
        ("envía {amount} dólares a {recipient}", "es", ["amount", "recipient"]),
        ("transfer {amount_en} dollars to {recipient_en}", "en", ["amount_en", "recipient_en"]),
        ("send {amount_en} to {recipient_en}", "en", ["amount_en", "recipient_en"]),
    ],
    "pay_bills": [
        ("paga el recibo de {bill}", "es", ["bill"]),
        ("pagar la factura de {bill}", "es", ["bill"]),
        ("pay the {bill_en} bill", "en", ["bill_en"]),
        ("pay my {bill_en}", "en", ["bill_en"]),
    ],
    "get_exchange_rate": [
        ("tipo de cambio de {currency} a {currency}", "es", ["currency"]),
        ("cuánto es {amount} dólares en soles", "es", ["amount"]),
        ("exchange rate {currency_en} to {currency_en}", "en", ["currency_en"]),
    ],
    "meditation": [
        ("guíame en una meditación de {duration}", "es", ["duration"]),
        ("medita conmigo {duration}", "es", ["duration"]),
        ("guide me in a {duration_en} meditation", "en", ["duration_en"]),
        ("meditate with me for {duration_en}", "en", ["duration_en"]),
    ],
    "translate_text": [
        ("traduce {phrase} a {language}", "es", ["phrase", "language"]),
        ("traduce al {language}", "es", ["language"]),
        ("translate {phrase_en} to {language_en}", "en", ["phrase_en", "language_en"]),
        ("translate to {language_en}", "en", ["language_en"]),
    ],
    "directions": [
        ("cómo llego a {city}", "es", ["city"]),
        ("direcciones a {city}", "es", ["city"]),
        ("how do I get to {city_en}", "en", ["city_en"]),
        ("directions to {city_en}", "en", ["city_en"]),
    ],
    "traffic_info": [
        ("cómo está el tráfico en {city}", "es", ["city"]),
        ("tráfico en {city}", "es", ["city"]),
        ("how's the traffic in {city_en}", "en", ["city_en"]),
        ("traffic in {city_en}", "en", ["city_en"]),
    ],
    "book_ride": [
        ("pide un uber a {city}", "es", ["city"]),
        ("taxi a {city}", "es", ["city"]),
        ("book an uber to {city_en}", "en", ["city_en"]),
        ("taxi to {city_en}", "en", ["city_en"]),
    ],
    "flight_booking": [
        ("reserva un vuelo a {city}", "es", ["city"]),
        ("vuelos a {city}", "es", ["city"]),
        ("book a flight to {city_en}", "en", ["city_en"]),
        ("flights to {city_en}", "en", ["city_en"]),
    ],
    "hotel_booking": [
        ("reserva un hotel en {city}", "es", ["city"]),
        ("hotel en {city}", "es", ["city"]),
        ("book a hotel in {city_en}", "en", ["city_en"]),
        ("hotels in {city_en}", "en", ["city_en"]),
    ],
    "time_query": [
        ("cuál es la hora", "es", []),
        ("me puedes decir la hora", "es", []),
        ("qué hora es en este momento", "es", []),
        ("what's the current time", "en", []),
        ("do you know what time it is", "en", []),
    ],
    "date_query": [
        ("cuál es la fecha de hoy", "es", []),
        ("en qué día estamos", "es", []),
        ("qué fecha estamos", "es", []),
        ("what is today's date", "en", []),
        ("what day are we on", "en", []),
    ],
    "help_query": [
        ("necesito ayuda", "es", []),
        ("cuéntame qué haces", "es", []),
        ("i need help", "en", []),
        ("tell me what you can do", "en", []),
    ],
    "system_control": [
        ("apaga el equipo", "es", []),
        ("reinicia la computadora", "es", []),
        ("hiberna el sistema", "es", []),
        ("shut down the pc", "en", []),
        ("put the computer to sleep", "en", []),
    ],
    "change_name": [
        ("llámame {new_name}", "es", ["new_name"]),
        ("quiero que te llames {new_name}", "es", ["new_name"]),
        ("call me {new_name_en}", "en", ["new_name_en"]),
        ("i will call you {new_name_en}", "en", ["new_name_en"]),
    ],
    "exit": [
        ("apaga el sistema", "es", []),
        ("me voy", "es", []),
        ("nos vemos", "es", []),
        ("i'm leaving", "en", []),
        ("see you later", "en", []),
        ("that's all", "en", []),
    ],
    "play_games": [
        ("juguemos a {game}", "es", ["game"]),
        ("pon un {game}", "es", ["game"]),
        ("let's play {game_en}", "en", ["game_en"]),
        ("play {game_en} with me", "en", ["game_en"]),
    ],
    "take_screenshot": [
        ("captura {location}", "es", ["location"]),
        ("haz una captura de {location}", "es", ["location"]),
        ("screenshot {location_en}", "en", ["location_en"]),
        ("take a screenshot of {location_en}", "en", ["location_en"]),
    ],
    "record_video": [
        ("graba un video de {video_topic}", "es", ["video_topic"]),
        ("record a {video_topic_en} video", "en", ["video_topic_en"]),
    ],
    "lock_door": [
        ("cierra {door}", "es", ["door"]),
        ("traba {door}", "es", ["door"]),
        ("lock {door_en}", "en", ["door_en"]),
        ("close {door_en}", "en", ["door_en"]),
    ],
    "unlock_door": [
        ("abre {door}", "es", ["door"]),
        ("desbloquea {door}", "es", ["door"]),
        ("unlock {door_en}", "en", ["door_en"]),
        ("open {door_en}", "en", ["door_en"]),
    ],
    "close_curtains": [
        ("cierra las cortinas de {room}", "es", ["room"]),
        ("close the curtains in {room_en}", "en", ["room_en"]),
    ],
    "open_curtains": [
        ("abre las cortinas de {room}", "es", ["room"]),
        ("corre las cortinas de {room}", "es", ["room"]),
        ("open the curtains in {room_en}", "en", ["room_en"]),
    ],
    "sleep_tracking": [
        ("cómo fue mi sueño {sleep_metric}", "es", ["sleep_metric"]),
        ("horas de sueño {sleep_metric}", "es", ["sleep_metric"]),
        ("how was my sleep {sleep_metric_en}", "en", ["sleep_metric_en"]),
        ("sleep hours {sleep_metric_en}", "en", ["sleep_metric_en"]),
    ],
    "check_investments": [
        ("cuánto tengo en {investment_type}", "es", ["investment_type"]),
        ("revisa mis {investment_type}", "es", ["investment_type"]),
        ("how much do I have in {investment_type_en}", "en", ["investment_type_en"]),
    ],
    "budget_report": [
        ("gastos de {period}", "es", ["period"]),
        ("reporte de gastos de {period}", "es", ["period"]),
        ("expenses for {period_en}", "en", ["period_en"]),
    ],
    "crypto_price": [
        ("precio de {coin}", "es", ["coin"]),
        ("cuánto vale {coin}", "es", ["coin"]),
        ("{coin_en} price", "en", ["coin_en"]),
    ],
    "water_reminder": [
        ("recuérdame tomar agua en {duration}", "es", ["duration"]),
        ("tomar agua cada {duration}", "es", ["duration"]),
        ("drink water every {duration_en}", "en", ["duration_en"]),
    ],
    "fitness_tracking": [
        ("mis pasos de hoy", "es", []),
        ("mi entrenamiento de hoy", "es", []),
        ("my steps today", "en", []),
        ("my workout today", "en", []),
    ],
    "health_stats": [
        ("cuál es mi {stat_type}", "es", ["stat_type"]),
        ("dame mi {stat_type}", "es", ["stat_type"]),
        ("what is my {stat_type_en}", "en", ["stat_type_en"]),
    ],
    "calendar_event": [
        ("muéstrame mi agenda de hoy", "es", []),
        ("qué tengo mañana", "es", []),
        ("show me today's agenda", "en", []),
        ("what do I have tomorrow", "en", []),
    ],
}


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def get_intent(name: str) -> Optional[Dict[str, object]]:
    """Retorna la intención por nombre, o None si no existe."""
    return INTENT_CATALOG.get(name)


def get_all_intents() -> List[Dict[str, object]]:
    """Retorna la lista de todas las intenciones del catálogo."""
    return list(INTENT_CATALOG.values())


def get_intents_by_category(category: str) -> List[Dict[str, object]]:
    """Retorna las intenciones de una categoría."""
    return [i for i in INTENT_CATALOG.values() if i["category"] == category]


def get_categories() -> Dict[str, List[str]]:
    """Retorna {categoría: [nombres de intenciones]}."""
    result: Dict[str, List[str]] = {}
    for intent in INTENT_CATALOG.values():
        result.setdefault(intent["category"], []).append(intent["name"])
    return result


def catalog_stats() -> Dict[str, object]:
    """Estadísticas del catálogo (total, por categoría, idiomas)."""
    by_category = {}
    for intent in INTENT_CATALOG.values():
        cat = intent["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    total_patterns = sum(
        len(intent["patterns_es"]) + len(intent["patterns_en"])
        for intent in INTENT_CATALOG.values()
    )
    return {
        "total_intents": len(INTENT_CATALOG),
        "categories": len(CATEGORIES),
        "by_category": by_category,
        "total_patterns": total_patterns,
        "has_es": all(intent["patterns_es"] and intent["variations_es"] for intent in INTENT_CATALOG.values()),
        "has_en": all(intent["patterns_en"] and intent["variations_en"] for intent in INTENT_CATALOG.values()),
    }


# ─────────────────────────────────────────────────────────────
# GENERADOR DE DATASET DE ENTRENAMIENTO
# ─────────────────────────────────────────────────────────────

def _expand_template(template: str, slots: List[str]) -> List[str]:
    """Expande una plantilla con los valores de FILLERS.

    Si la plantilla tiene un solo slot, genera una frase por valor.
    Si tiene dos slots, genera la combinación (mantiene el dataset razonable).
    """
    if not slots:
        return [template]

    values_lists = [FILLERS.get(s, [f"[{s}]"]) for s in slots]

    # Combinación de slots: producto cartesiano limitado para no explotar
    if len(slots) == 2:
        results = []
        for v0 in values_lists[0]:
            for v1 in values_lists[1]:
                results.append(template.format(**{slots[0]: v0, slots[1]: v1}))
        return results

    return [template.format(**{slots[0]: v}) for v in values_lists[0]]


def generate_training_data(min_examples: int = 1000) -> List[Dict[str, str]]:
    """Genera el dataset bilingüe de entrenamiento.

    Combina las variaciones literales (semilla) con la expansión de plantillas.
    Retorna una lista de {"text", "intent", "lang"} sin duplicados.
    """
    dataset: Dict[str, str] = {}

    for intent in INTENT_CATALOG.values():
        name = intent["name"]

        # Semilla: variaciones literales
        for variation in intent["variations_es"]:
            dataset[(variation, name, "es")] = name
        for variation in intent["variations_en"]:
            dataset[(variation, name, "en")] = name

        # Expansión con plantillas
        for template, lang, slots in TEMPLATES.get(name, []):
            for phrase in _expand_template(template, slots):
                dataset[(phrase, name, lang)] = name

    # Si aún no alcanzamos el mínimo, añadimos variaciones con saludo/firma
    result = [
        {"text": text, "intent": intent, "lang": lang}
        for (text, intent, lang) in dataset
    ]
    result.sort(key=lambda x: x["text"])

    if len(result) < min_examples:
        extra = _generate_extra_examples(min_examples - len(result))
        result.extend(extra)
        result.sort(key=lambda x: x["text"])

    # Garantiza un piso de ejemplos por intención para clases pequeñas
    result = _ensure_min_per_intent(result)
    result.sort(key=lambda x: x["text"])

    return result


def _ensure_min_per_intent(
    dataset: List[Dict[str, str]],
    min_per_intent: int = 16,
) -> List[Dict[str, str]]:
    """Sube con variantes de saludo las intenciones con pocos ejemplos."""
    counts: Dict[str, int] = {}
    for example in dataset:
        counts[example["intent"]] = counts.get(example["intent"], 0) + 1

    if all(count >= min_per_intent for count in counts.values()):
        return dataset

    greetings_es = ["oye", "por favor", "hey"]
    greetings_en = ["hey", "please", "could you"]
    seen = set((e["text"], e["intent"], e["lang"]) for e in dataset)
    result = list(dataset)

    for name, count in counts.items():
        if count >= min_per_intent:
            continue
        intent = INTENT_CATALOG[name]
        need = min_per_intent - count
        for lang, greetings, variations in (
            ("es", greetings_es, intent["variations_es"]),
            ("en", greetings_en, intent["variations_en"]),
        ):
            for greeting in greetings:
                for base in variations:
                    if need <= 0:
                        break
                    text = f"{greeting}, {base}"
                    key = (text, name, lang)
                    if key not in seen:
                        seen.add(key)
                        result.append({"text": text, "intent": name, "lang": lang})
                        need -= 1

    return result


def _generate_extra_examples(count: int) -> List[Dict[str, str]]:
    """Genera ejemplos adicionales variando el inicio/saludo de frases existentes."""
    greetings_es = ["oye", "por favor", "hey"]
    greetings_en = ["hey", "please", "could you"]
    extra = []
    used = set()
    intents = list(INTENT_CATALOG.values())

    while len(extra) < count:
        intent = intents[len(extra) % len(intents)]
        name = intent["name"]

        if len(extra) % 2 == 0 and intent["variations_es"]:
            base = intent["variations_es"][len(extra) // 2 % len(intent["variations_es"])]
            greeting = greetings_es[len(extra) % len(greetings_es)]
            text = f"{greeting}, {base}"
            lang = "es"
        elif intent["variations_en"]:
            base = intent["variations_en"][len(extra) // 2 % len(intent["variations_en"])]
            greeting = greetings_en[len(extra) % len(greetings_en)]
            text = f"{greeting}, {base}"
            lang = "en"
        else:
            continue

        key = (text, name, lang)
        if key not in used:
            used.add(key)
            extra.append({"text": text, "intent": name, "lang": lang})

    return extra


def get_training_data() -> List[Dict[str, str]]:
    """Retorna el dataset de entrenamiento (cacheado)."""
    if not getattr(get_training_data, "_cache", None):
        get_training_data._cache = generate_training_data(min_examples=1000)
    return get_training_data._cache


def training_stats(dataset: Optional[List[Dict[str, str]]] = None) -> Dict[str, object]:
    """Estadísticas del dataset: total, por idioma y por categoría."""
    if dataset is None:
        dataset = get_training_data()

    by_lang: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    by_intent: Dict[str, int] = {}

    for example in dataset:
        lang = example["lang"]
        name = example["intent"]
        by_lang[lang] = by_lang.get(lang, 0) + 1
        by_intent[name] = by_intent.get(name, 0) + 1
        intent = INTENT_CATALOG.get(name)
        if intent:
            category = intent["category"]
            by_category[category] = by_category.get(category, 0) + 1

    return {
        "total": len(dataset),
        "by_lang": by_lang,
        "by_category": by_category,
        "intents_covered": len(by_intent),
    }
