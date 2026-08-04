"""
orchestrator.py - El Director de Orquesta de Jarvis

Conecta TODOS los módulos de Semana 1 y 2:
- core/config.py          → Configuración
- core/logger.py          → Logging
- core/intent_recognizer.py → Reconocimiento de intenciones
- brain/memory.py         → Memoria
- brain/decision.py       → Motor de decisiones
- orchestrator/events.py  → Sistema de eventos
- orchestrator/errors.py  → Manejo de errores

Flujo completo:
    Usuario habla
        ↓
    takecommand() escucha
        ↓
    IntentRecognizer detecta intención
        ↓
    MemoryManager busca contexto
        ↓
    DecisionEngine decide qué agente activar
        ↓
    Orchestrator ejecuta la acción
        ↓
    speak() responde al usuario
        ↓
    MemoryManager guarda la interacción

Filosofía:
- Mejor lento y bien, que rápido y mal
- La arquitectura es más importante que el código
- Cada línea debe servir para aprender y crecer
"""

import datetime
import os
import random
import webbrowser as wb
from enum import Enum
from typing import Any, Dict, Optional

import pyjokes
import pyautogui
import pyttsx3
import speech_recognition as sr
import wikipedia

try:
    from .core.config import get_config
    from .core.logger import JarvisLogger, AgentLogger
    from .core.intent_recognizer import IntentRecognizer, Intent
    from .brain.memory import MemoryManager
    from .brain.decision import DecisionEngine, DecisionContext
    from .orchestrator.events import (
        EventBus, JarvisEvent, EventPriority,
        get_event_bus, init_event_bus
    )
    from .orchestrator.errors import (
        ErrorHandler, RecoveryStrategy,
        get_error_handler
    )
except ImportError:
    from core.config import get_config
    from core.logger import JarvisLogger, AgentLogger
    from core.intent_recognizer import IntentRecognizer, Intent
    from brain.memory import MemoryManager
    from brain.decision import DecisionEngine, DecisionContext
    from orchestrator.events import (
        EventBus, JarvisEvent, EventPriority,
        get_event_bus, init_event_bus
    )
    from orchestrator.errors import (
        ErrorHandler, RecoveryStrategy,
        get_error_handler
    )


# ══════════════════════════════════════════════════
# ESTADOS DE JARVIS
# ══════════════════════════════════════════════════

class JarvisState(Enum):
    """
    Estados posibles de Jarvis en cada momento.
    La esfera visual reacciona a cada estado.

    IDLE       → Azul tranquilo, esperando
    LISTENING  → Verde pulsante, escuchando
    THINKING   → Amarillo agitado, procesando
    SPEAKING   → Azul brillante, respondiendo
    ERROR      → Rojo, algo salió mal
    STOPPING   → Apagándose
    """
    IDLE        = "idle"
    LISTENING   = "listening"
    THINKING    = "thinking"
    SPEAKING    = "speaking"
    ERROR       = "error"
    STOPPING    = "stopping"


# ══════════════════════════════════════════════════
# ORQUESTADOR PRINCIPAL
# ══════════════════════════════════════════════════

class Orchestrator:
    """
    El Director de Orquesta de Jarvis.

    Responsabilidades:
    - Inicializar todos los módulos al arrancar
    - Recibir input del usuario (voz)
    - Coordinar el flujo completo de cada interacción
    - Publicar eventos para cada paso
    - Manejar errores y recuperarse
    - Mantener el estado de Jarvis

    Uso:
        orchestrator = Orchestrator()
        orchestrator.run()
    """

    def __init__(self, config=None):
        """
        Inicializa el Orquestador y todos sus módulos.

        Args:
            config: Configuración (usa get_config() si None)
        """
        # Configuración
        self.config = config or get_config()

        # Logger
        self.logger = AgentLogger("orchestrator", "orch_001")
        self.logger.info("Initializing Orchestrator...")

        # Estado actual
        self.state = JarvisState.IDLE
        self.is_running = False

        # Motor de voz (pyttsx3)
        self._engine = None
        self._init_voice_engine()

        # Inicializar todos los módulos
        self._init_modules()

        self.logger.info("Orchestrator ready")

    # ── Inicialización ───────────────────────────

    def _init_voice_engine(self) -> None:
        """Inicializa el motor de voz pyttsx3."""
        try:
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty('voices')
            self._engine.setProperty('voice', voices[1].id)
            self._engine.setProperty('rate', self.config.voice.rate)
            self._engine.setProperty('volume', self.config.voice.volume)
            self.logger.info("Voice engine initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize voice engine: {e}")
            self._engine = None

    def _init_modules(self) -> None:
        """
        Inicializa todos los módulos de Jarvis.
        Si alguno falla, continúa con los demás.
        """
        # EventBus — primero, todos lo necesitan
        try:
            self.event_bus = init_event_bus()
            self.logger.info("EventBus initialized")
        except Exception as e:
            self.logger.error(f"EventBus failed: {e}")
            self.event_bus = None

        # ErrorHandler
        try:
            self.error_handler = get_error_handler()
            self.logger.info("ErrorHandler initialized")
        except Exception as e:
            self.logger.error(f"ErrorHandler failed: {e}")
            self.error_handler = None

        # Memoria
        try:
            self.memory = MemoryManager()
            self.logger.info("MemoryManager initialized")
        except Exception as e:
            self.logger.warning(f"MemoryManager failed (non-critical): {e}")
            self.memory = None

        # Reconocedor de intenciones
        try:
            self.intent_recognizer = IntentRecognizer()
            self.logger.info("IntentRecognizer initialized")
        except Exception as e:
            self.logger.error(f"IntentRecognizer failed: {e}")
            self.intent_recognizer = None

        # Motor de decisiones
        try:
            self.decision_engine = DecisionEngine()
            self.logger.info("DecisionEngine initialized")
        except Exception as e:
            self.logger.error(f"DecisionEngine failed: {e}")
            self.decision_engine = None

        # Suscribir eventos internos
        self._subscribe_events()

        # Publicar evento de sistema listo
        self._publish(JarvisEvent.SYSTEM_READY, {"modules": "all"})

    def _subscribe_events(self) -> None:
        """Suscribe el orquestador a los eventos que le interesan."""
        if not self.event_bus:
            return

        self.event_bus.subscribe(
            JarvisEvent.ERROR_CRITICAL,
            self._handle_critical_error
        )
        self.event_bus.subscribe(
            JarvisEvent.SESSION_ENDED,
            self._handle_session_end
        )

    # ── Flujo principal ──────────────────────────

    def run(self) -> None:
        """
        Loop principal de Jarvis.
        Escucha, procesa y responde continuamente.
        """
        self.is_running = True
        self._publish(JarvisEvent.SESSION_STARTED, {})

        self.logger.info("Jarvis started — entering main loop")
        self._wishme()

        while self.is_running:
            try:
                # 1. Escuchar al usuario
                user_input = self._listen()
                if not user_input:
                    continue

                # 2. Procesar input completo
                response = self.process_input(user_input)

                # 3. Responder si hay respuesta
                if response:
                    self.speak(response)

            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received")
                break
            except Exception as e:
                self._handle_error(e, "main_loop")

        self.stop()

    def process_input(self, user_input: str) -> Optional[str]:
        """
        Procesa el input del usuario de principio a fin.

        Flujo:
        1. Publicar evento de input recibido
        2. Guardar en memoria
        3. Reconocer intención
        4. Tomar decisión
        5. Ejecutar acción
        6. Guardar resultado en memoria
        7. Retornar respuesta

        Args:
            user_input: Lo que dijo el usuario

        Returns:
            Respuesta de Jarvis (texto) o None
        """
        self._set_state(JarvisState.THINKING)
        self._publish(JarvisEvent.USER_INPUT_RECEIVED, {"text": user_input})

        self.logger.info(f"Processing: '{user_input}'")

        try:
            # Paso 1: Guardar input en memoria
            if self.memory:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(
                        self.memory.save(
                            key=f"input_{datetime.datetime.now().timestamp():.0f}",
                            value=user_input,
                            importance="normal"
                        )
                    )
                except Exception:
                    pass

            # Paso 2: Reconocer intención
            intent = self._recognize_intent(user_input)
            if not intent:
                return "Lo siento, no pude entender eso."

            # Paso 3: Ejecutar acción según intención
            response = self._execute_intent(intent, user_input)

            # Paso 4: Guardar conversación en memoria
            if self.memory and response:
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(
                        self.memory.save_conversation(
                            user_message=user_input,
                            agent_response=response,
                            intent=intent.name
                        )
                    )
                except Exception:
                    pass

            self._publish(JarvisEvent.USER_INPUT_PROCESSED, {
                "input": user_input,
                "intent": intent.name,
                "response": response
            })

            return response

        except Exception as e:
            self._handle_error(e, "process_input", {"input": user_input})
            return "Ocurrió un error procesando tu solicitud."

        finally:
            self._set_state(JarvisState.IDLE)

    # ── Voz ──────────────────────────────────────

    def speak(self, text: str) -> None:
        """
        Hace que Jarvis hable.

        Args:
            text: Texto a hablar
        """
        self._set_state(JarvisState.SPEAKING)
        self._publish(JarvisEvent.USER_RESPONSE_READY, {"text": text})

        print(f"Jarvis: {text}")

        try:
            if self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
        except Exception as e:
            self.logger.error(f"Speech error: {e}")
        finally:
            self._set_state(JarvisState.IDLE)

    def _listen(self) -> Optional[str]:
        """
        Escucha al usuario por micrófono.

        Returns:
            Texto reconocido o None si no se pudo escuchar
        """
        self._set_state(JarvisState.LISTENING)
        self._publish(JarvisEvent.INTENT_RECOGNITION_STARTED, {})

        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("Escuchando...")
                r.pause_threshold = 1
                audio = r.listen(source, timeout=self.config.voice.timeout)

            print("Reconociendo...")
            text = r.recognize_google(audio, language=self.config.voice.language)
            print(f"Tú: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            self._set_state(JarvisState.IDLE)
            return None
        except sr.UnknownValueError:
            self.speak("Lo siento, no entendí eso.")
            return None
        except sr.RequestError:
            self.speak("El servicio de reconocimiento no está disponible.")
            return None
        except Exception as e:
            self._handle_error(e, "listen")
            return None
        finally:
            if self.state == JarvisState.LISTENING:
                self._set_state(JarvisState.IDLE)

    # ── Intención y ejecución ────────────────────

    def _recognize_intent(self, user_input: str) -> Optional[Intent]:
        """
        Reconoce la intención del usuario.

        Args:
            user_input: Input del usuario

        Returns:
            Intent reconocido o None
        """
        if not self.intent_recognizer:
            self.logger.warning("IntentRecognizer not available")
            return None

        try:
            intent = self.intent_recognizer.recognize(user_input)
            self._publish(JarvisEvent.INTENT_RECOGNIZED, {
                "intent": intent.name,
                "confidence": intent.confidence,
                "entities": intent.entities
            })
            return intent

        except Exception as e:
            self._handle_error(e, "intent_recognizer", {"input": user_input})
            return None

    def _execute_intent(self, intent: Intent, user_input: str) -> Optional[str]:
        """
        Ejecuta la acción correspondiente a la intención detectada.

        Mapeo de intenciones a acciones:
        - time_query      → decir la hora
        - date_query      → decir la fecha
        - play_music      → reproducir música
        - watch_videos    → abrir YouTube
        - search_info     → buscar en Wikipedia
        - open_application → abrir aplicación
        - take_screenshot → captura de pantalla
        - tell_joke       → contar chiste
        - system_control  → control del sistema
        - change_name     → cambiar nombre
        - exit            → salir

        Args:
            intent: Intención reconocida
            user_input: Input original del usuario

        Returns:
            Respuesta de texto o None
        """
        self._publish(JarvisEvent.ACTION_EXECUTING, {
            "intent": intent.name,
            "confidence": intent.confidence
        })

        try:
            response = None

            if intent.name == "time_query":
                response = self._action_time()

            elif intent.name == "date_query":
                response = self._action_date()

            elif intent.name == "play_music":
                genre = intent.entities.get("genre", "")
                response = self._action_play_music(genre)

            elif intent.name == "watch_videos":
                response = self._action_open_youtube()

            elif intent.name == "search_info":
                query = user_input.replace("wikipedia", "").replace("busca", "").strip()
                response = self._action_search_wikipedia(query)

            elif intent.name == "open_application":
                app = intent.entities.get("platform", "google")
                response = self._action_open_app(app)

            elif intent.name == "take_screenshot":
                response = self._action_screenshot()

            elif intent.name == "tell_joke":
                response = self._action_tell_joke()

            elif intent.name == "system_control":
                action = intent.entities.get("action", "")
                response = self._action_system_control(action)

            elif intent.name == "change_name":
                response = self._action_change_name()

            elif intent.name == "exit":
                response = self._action_exit()

            else:
                response = "Comando no reconocido. Por favor intente de nuevo."

            self._publish(JarvisEvent.ACTION_COMPLETED, {
                "intent": intent.name,
                "response": response
            })

            return response

        except Exception as e:
            self._publish(JarvisEvent.ACTION_FAILED, {
                "intent": intent.name,
                "error": str(e)
            })
            self._handle_error(e, f"action_{intent.name}")
            return "Ocurrió un error ejecutando esa acción."

    # ── Acciones ─────────────────────────────────

    def _action_time(self) -> str:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        return f"La hora actual es {current_time}"

    def _action_date(self) -> str:
        now = datetime.datetime.now()
        return f"La fecha actual es {now.day} de {now.strftime('%B')} de {now.year}"

    def _action_play_music(self, song_name: str = "") -> str:
        song_dir = os.path.expanduser("~\\Music")
        try:
            songs = os.listdir(song_dir)
            if song_name:
                songs = [s for s in songs if song_name.lower() in s.lower()]
            if songs:
                song = random.choice(songs)
                os.startfile(os.path.join(song_dir, song))
                return f"Reproduciendo {song}"
            return "No se encontró ninguna canción."
        except Exception:
            return "No pude acceder a la carpeta de música."

    def _action_open_youtube(self) -> str:
        wb.open("youtube.com")
        return "Abriendo YouTube."

    def _action_search_wikipedia(self, query: str) -> str:
        try:
            wikipedia.set_lang("es")
            result = wikipedia.summary(query, sentences=2)
            return result
        except wikipedia.exceptions.DisambiguationError:
            return "Hay varios resultados. Por favor sea más específico."
        except Exception:
            return "No encontré nada en Wikipedia."

    def _action_open_app(self, app: str) -> str:
        apps = {
            "google": "google.com",
            "youtube": "youtube.com",
            "github": "github.com"
        }
        url = apps.get(app.lower())
        if url:
            wb.open(url)
            return f"Abriendo {app}."
        return f"No sé cómo abrir {app}."

    def _action_screenshot(self) -> str:
        try:
            img = pyautogui.screenshot()
            img_path = os.path.expanduser("~\\Pictures\\captura.png")
            img.save(img_path)
            return f"Captura guardada en {img_path}"
        except Exception:
            return "No pude tomar la captura de pantalla."

    def _action_tell_joke(self) -> str:
        try:
            return pyjokes.get_joke(language="es")
        except Exception:
            return "No se me ocurre ningún chiste ahora mismo."

    def _action_system_control(self, action: str) -> str:
        if "apagar" in action:
            self.speak("Apagando el sistema, hasta luego!")
            os.system("shutdown /s /f /t 5")
            self.is_running = False
            return None
        elif "reiniciar" in action:
            self.speak("Reiniciando el sistema, por favor espere!")
            os.system("shutdown /r /f /t 5")
            self.is_running = False
            return None
        return "Acción de sistema no reconocida."

    def _action_change_name(self) -> str:
        self.speak("¿Cómo le gustaría llamarme?")
        name = self._listen()
        if name:
            with open("assistant_name.txt", "w") as f:
                f.write(name)
            return f"De acuerdo, a partir de ahora me llamaré {name}."
        return "Lo siento, no pude escuchar el nombre."

    def _action_exit(self) -> str:
        self.is_running = False
        return "Desconectándome. ¡Que tenga un buen día!"

    # ── Utilidades ───────────────────────────────

    def _wishme(self) -> None:
        """Saludo inicial según la hora."""
        hour = datetime.datetime.now().hour
        name = self._load_name()

        if 4 <= hour < 12:
            greeting = "Buenos días"
        elif 12 <= hour < 16:
            greeting = "Buenas tardes"
        else:
            greeting = "Buenas noches"

        self.speak(f"Bienvenido de nuevo, señor! {greeting}!")
        self.speak(f"{name} a su servicio. ¿En qué le puedo ayudar?")

    def _load_name(self) -> str:
        """Carga el nombre de Jarvis desde archivo."""
        try:
            with open("assistant_name.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return self.config.system.name

    def _set_state(self, state: JarvisState) -> None:
        """Actualiza el estado de Jarvis."""
        self.state = state
        self.logger.debug(f"State: {state.value}")

    def _publish(self, event_type: JarvisEvent, data: Dict[str, Any]) -> None:
        """Publica un evento al EventBus de forma segura."""
        try:
            if self.event_bus:
                self.event_bus.publish(event_type, "orchestrator", data)
        except Exception:
            pass

    def _handle_error(
        self,
        error: Exception,
        source: str,
        context: Dict[str, Any] = None
    ) -> None:
        """Maneja un error usando el ErrorHandler."""
        self._set_state(JarvisState.ERROR)

        if self.error_handler:
            self.error_handler.handle(error, source, context)
        else:
            self.logger.error(f"Error in {source}: {error}")

        self._set_state(JarvisState.IDLE)

    def _handle_critical_error(self, event) -> None:
        """Responde a eventos de error crítico."""
        self.logger.critical(f"Critical error received: {event.data}")
        self.speak("Jarvis ha encontrado un error crítico. Reiniciando...")
        self.is_running = False

    def _handle_session_end(self, event) -> None:
        """Responde al evento de fin de sesión."""
        self.logger.info("Session ended")
        self.is_running = False

    def stop(self) -> None:
        """Detiene Jarvis de forma segura."""
        self.logger.info("Stopping Jarvis...")
        self._set_state(JarvisState.STOPPING)
        self._publish(JarvisEvent.SESSION_ENDED, {})
        self._publish(JarvisEvent.SYSTEM_STOPPING, {})

        if self.event_bus:
            self.event_bus.stop()

        self.logger.info("Jarvis stopped")

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado completo del sistema."""
        return {
            "state": self.state.value,
            "is_running": self.is_running,
            "modules": {
                "event_bus": self.event_bus is not None,
                "memory": self.memory is not None,
                "intent_recognizer": self.intent_recognizer is not None,
                "decision_engine": self.decision_engine is not None,
                "error_handler": self.error_handler is not None
            },
            "event_stats": self.event_bus.get_stats() if self.event_bus else {},
            "error_stats": self.error_handler.get_stats() if self.error_handler else {}
        }

    def __repr__(self) -> str:
        return f"Orchestrator(state={self.state.value}, running={self.is_running})"


# ══════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════

def main():
    """Punto de entrada principal de Jarvis."""
    logger = JarvisLogger.get_logger("main")
    logger.info("Starting Jarvis AGI...")

    try:
        orchestrator = Orchestrator()
        orchestrator.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
