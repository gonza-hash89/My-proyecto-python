"""
Intent Recognizer - Reconoce la intención detrás de lo que dice el usuario
No busca comandos exactos, sino entiende QUÉ quiere el usuario
"""

from typing import Dict, List, Tuple, Any
import logging
from dataclasses import dataclass


@dataclass
class Intent:
    """Representa una intención detectada"""
    name: str                          # Ej: "watch_videos", "play_music"
    confidence: float                  # 0-1, qué tan seguro estamos
    entities: Dict[str, str]           # Ej: {"platform": "youtube", "topic": "programming"}
    raw_input: str                     # Lo que dijo el usuario
    
    def __repr__(self):
        return f"Intent(name={self.name}, confidence={self.confidence:.2f}, entities={self.entities})"


class IntentRecognizer:
    """
    Reconoce intenciones del usuario usando fuzzy matching y reglas semánticas.
    
    Ejemplo:
        "abrir youtube" → Intent(name="watch_videos", entities={"platform": "youtube"})
        "pon música" → Intent(name="play_music", entities={})
        "quiero ver videos de programación" → Intent(name="watch_videos", entities={"topic": "programming"})
    """

    def __init__(self):
        """Inicializa el reconocedor de intenciones"""
        self.logger = logging.getLogger("Jarvis.IntentRecognizer")
        
        # Definir intenciones y sus palabras clave asociadas
        self.intent_keywords = {
            "watch_videos": {
                "keywords": ["youtube", "video", "ver", "watch", "viralizar", "película", "película"],
                "variations": [
                    "abrir youtube",
                    "pon videos",
                    "quiero ver videos",
                    "reproducir video",
                    "abre youtube",
                    "mira videos"
                ],
                "entities": ["platform", "topic", "duration"]
            },
            
            "play_music": {
                "keywords": ["música", "music", "canción", "song", "reproducir", "play", "pon"],
                "variations": [
                    "reproducir música",
                    "pon música",
                    "toca música",
                    "música",
                    "quiero escuchar",
                    "pon una canción"
                ],
                "entities": ["artist", "genre", "playlist", "song_name"]
            },
            
            "search_info": {
                "keywords": ["buscar", "search", "wikipedia", "información", "info", "quién", "qué", "cuándo", "dónde"],
                "variations": [
                    "busca en wikipedia",
                    "quién es",
                    "qué es",
                    "búscame información",
                    "dame datos de"
                ],
                "entities": ["topic", "source", "detail_level"]
            },
            
            "open_application": {
                "keywords": ["abrir", "open", "abre", "lanza", "launch", "ejecuta"],
                "variations": [
                    "abrir google",
                    "abre chrome",
                    "abre visual studio",
                    "lanza el navegador",
                    "ejecuta word"
                ],
                "entities": ["application", "parameters"]
            },
            
            "system_control": {
                "keywords": ["apagar", "shutdown", "reiniciar", "restart", "bloquear", "lock", "dormr", "sleep"],
                "variations": [
                    "apaga la máquina",
                    "reinicia el sistema",
                    "bloquea la pc",
                    "pon en dormir"
                ],
                "entities": ["action", "delay"]
            },
            
            "take_screenshot": {
                "keywords": ["captura", "screenshot", "pantalla", "captura de", "screenshot"],
                "variations": [
                    "toma una captura",
                    "captura de pantalla",
                    "screenshot",
                    "saca una foto de pantalla"
                ],
                "entities": ["format", "location"]
            },
            
            "tell_joke": {
                "keywords": ["chiste", "joke", "cuéntame", "dime", "reír", "risa"],
                "variations": [
                    "cuéntame un chiste",
                    "dime un chiste",
                    "necesito reír",
                    "dame un joke"
                ],
                "entities": ["topic"]
            },
            
            "time_query": {
                "keywords": ["hora", "time", "qué hora", "cuál es la hora"],
                "variations": [
                    "¿qué hora es?",
                    "hora",
                    "dime la hora",
                    "cuál es la hora"
                ],
                "entities": []
            },
            
            "date_query": {
                "keywords": ["fecha", "date", "qué fecha", "cuál es la fecha", "día"],
                "variations": [
                    "¿qué fecha es?",
                    "fecha",
                    "dime la fecha",
                    "cuál es hoy"
                ],
                "entities": []
            },
            
            "change_name": {
                "keywords": ["nombre", "name", "llamar", "call", "cambia", "change"],
                "variations": [
                    "cambia tu nombre",
                    "cómo te llamas",
                    "quiero llamarte",
                    "nuevo nombre"
                ],
                "entities": ["new_name"]
            },
            
            "exit": {
                "keywords": ["salir", "exit", "desconectar", "apagar", "bye", "adiós"],
                "variations": [
                    "desconéctate",
                    "ya no necesito",
                    "adiós jarvis",
                    "salir"
                ],
                "entities": []
            }
        }
        
        self.logger.info("IntentRecognizer initialized with {} intent types".format(
            len(self.intent_keywords)
        ))

    def recognize(self, user_input: str) -> Intent:
        """
        Reconoce la intención del usuario.

        Args:
            user_input: Lo que dijo el usuario

        Returns:
            Intent object con la intención detectada
        """
        user_input_lower = user_input.lower().strip()
        
        best_intent = None
        best_score = 0
        best_entities = {}

        # Buscar la mejor coincidencia
        for intent_name, intent_data in self.intent_keywords.items():
            score, entities = self._calculate_intent_score(
                user_input_lower,
                intent_data
            )

            if score > best_score:
                best_score = score
                best_intent = intent_name
                best_entities = entities

        # Si no encontramos nada bueno, retornar intención "unknown"
        if best_score < 0.3:
            self.logger.warning(f"Could not recognize intent for: {user_input}")
            return Intent(
                name="unknown",
                confidence=0.0,
                entities={},
                raw_input=user_input
            )

        # Retornar la mejor intención encontrada
        intent = Intent(
            name=best_intent,
            confidence=min(best_score, 1.0),
            entities=best_entities,
            raw_input=user_input
        )

        self.logger.info(f"Intent recognized: {intent}")
        return intent

    def _calculate_intent_score(self, user_input: str, intent_data: Dict) -> Tuple[float, Dict[str, str]]:
        """
        Calcula qué tan probable es que sea esta intención.

        Args:
            user_input: Input del usuario (lowercase)
            intent_data: Datos de la intención

        Returns:
            Tupla (score, entities)
        """
        keywords = intent_data.get("keywords", [])
        variations = intent_data.get("variations", [])
        
        score = 0.0
        entities = {}

        # Búsqueda 1: Palabras clave exactas (peso: 0.3 cada una)
        for keyword in keywords:
            if keyword in user_input:
                score += 0.3

        # Búsqueda 2: Variaciones exactas (peso: 0.8 si coincide)
        for variation in variations:
            if variation in user_input:
                score += 0.8
                break  # Una variación es suficiente

        # Búsqueda 3: Palabras clave parciales (peso: 0.15)
        words = user_input.split()
        for word in words:
            for keyword in keywords:
                if self._is_similar(word, keyword, threshold=0.8):
                    score += 0.15
                    break

        # Extraer entidades (palabras después de palabras clave)
        entities = self._extract_entities(user_input, intent_data)

        return score, entities

    def _is_similar(self, word1: str, word2: str, threshold: float = 0.8) -> bool:
        """
        Compara dos palabras usando Levenshtein distance.
        Permite typos y variaciones menores.

        Args:
            word1: Primera palabra
            word2: Segunda palabra
            threshold: Umbral de similitud (0-1)

        Returns:
            True si son similares
        """
        if word1 == word2:
            return True

        # Distancia Levenshtein simple
        distance = self._levenshtein_distance(word1, word2)
        max_len = max(len(word1), len(word2))

        similarity = 1 - (distance / max_len)
        return similarity >= threshold

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calcula la distancia Levenshtein entre dos strings"""
        if len(s1) < len(s2):
            return IntentRecognizer._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # j+1 porque previous_row y current_row están offset por uno en la comparación
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _extract_entities(self, user_input: str, intent_data: Dict) -> Dict[str, str]:
        """
        Extrae entidades (información adicional) del input.

        Ejemplo:
            Input: "pon música de rock"
            Entidades extraídas: {"genre": "rock"}

        Args:
            user_input: Input del usuario
            intent_data: Datos de la intención

        Returns:
            Diccionario con entidades encontradas
        """
        entities = {}
        entity_keywords = {
            "platform": ["youtube", "spotify", "google", "chrome", "firefox"],
            "topic": ["programación", "music", "news", "weather", "sports"],
            "genre": ["rock", "pop", "jazz", "clásico", "electrónica"],
            "artist": ["shakira", "bad bunny", "coldplay"],
            "action": ["apagar", "reiniciar", "bloquear", "dormir"],
        }

        words = user_input.split()
        for i, word in enumerate(words):
            for entity_type, keywords in entity_keywords.items():
                if word in keywords:
                    entities[entity_type] = word
                    # Si hay palabra siguiente, guardarla como contexto
                    if i + 1 < len(words):
                        entities[entity_type + "_context"] = words[i + 1]

        return entities

    def get_available_intents(self) -> List[str]:
        """Retorna lista de intenciones disponibles"""
        return list(self.intent_keywords.keys())

    def __repr__(self) -> str:
        return f"IntentRecognizer(intents={len(self.intent_keywords)})"
