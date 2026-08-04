"""
events.py - Sistema de eventos de Jarvis
El sistema nervioso que conecta todos los módulos.

Mejora sobre message_queue.py:
- Eventos tipados con Enum (no strings sueltos)
- Cola con prioridades (crítico va primero)
- Integración con JarvisLogger
- Soporte async/await
- Estadísticas detalladas por tipo de evento

Filosofía:
- Módulos no se conocen entre sí
- Se comunican SOLO por eventos
- Cada evento es trazable y registrado
"""

import asyncio
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import PriorityQueue
from typing import Any, Callable, Dict, List, Optional

try:
    from .logger import JarvisLogger, EventLogger
except ImportError:
    import logging
    class JarvisLogger:
        @classmethod
        def get_logger(cls, name):
            return logging.getLogger(f"Jarvis.{name}")
    class EventLogger:
        def __init__(self):
            self.logger = logging.getLogger("Jarvis.Events")
        def log_event(self, event_type, data=None):
            self.logger.info(f"EVENT: {event_type} | {data}")


# ══════════════════════════════════════════════════
# TIPOS DE EVENTOS
# ══════════════════════════════════════════════════

class JarvisEvent(Enum):
    """
    Todos los eventos posibles en Jarvis.
    Tipados para evitar errores de strings sueltos.

    Categorías:
    - USER_*    : Interacción del usuario
    - INTENT_*  : Reconocimiento de intención
    - DECISION_*: Motor de decisiones
    - ACTION_*  : Ejecución de acciones
    - MEMORY_*  : Sistema de memoria
    - SYSTEM_*  : Eventos del sistema
    - ERROR_*   : Errores y recuperación
    """

    # ── Usuario ──────────────────────────────────
    USER_INPUT_RECEIVED     = "user_input_received"
    USER_INPUT_PROCESSED    = "user_input_processed"
    USER_RESPONSE_READY     = "user_response_ready"

    # ── Intención ────────────────────────────────
    INTENT_RECOGNITION_STARTED  = "intent_recognition_started"
    INTENT_RECOGNIZED           = "intent_recognized"
    INTENT_AMBIGUOUS            = "intent_ambiguous"
    INTENT_REJECTED             = "intent_rejected"
    INTENT_UNKNOWN              = "intent_unknown"

    # ── Decisión ─────────────────────────────────
    DECISION_STARTED    = "decision_started"
    DECISION_MADE       = "decision_made"
    DECISION_CONFLICT   = "decision_conflict"
    DECISION_FAILED     = "decision_failed"

    # ── Acción ───────────────────────────────────
    ACTION_EXECUTING    = "action_executing"
    ACTION_COMPLETED    = "action_completed"
    ACTION_FAILED       = "action_failed"
    ACTION_RETRY        = "action_retry"

    # ── Memoria ──────────────────────────────────
    MEMORY_SAVED        = "memory_saved"
    MEMORY_RECALLED     = "memory_recalled"
    MEMORY_NOT_FOUND    = "memory_not_found"
    MEMORY_CLEARED      = "memory_cleared"

    # ── Sistema ──────────────────────────────────
    SYSTEM_STARTED      = "system_started"
    SYSTEM_READY        = "system_ready"
    SYSTEM_STOPPING     = "system_stopping"
    SESSION_STARTED     = "session_started"
    SESSION_ENDED       = "session_ended"
    AGENT_REGISTERED    = "agent_registered"
    AGENT_UNREGISTERED  = "agent_unregistered"

    # ── Error ────────────────────────────────────
    ERROR_OCCURRED      = "error_occurred"
    ERROR_RECOVERED     = "error_recovered"
    ERROR_CRITICAL      = "error_critical"


class EventPriority(Enum):
    """
    Prioridades de eventos.
    Los eventos críticos van primero en la cola.
    """
    CRITICAL    = 1  # Errores críticos, shutdown
    HIGH        = 2  # Acciones importantes
    NORMAL      = 3  # Flujo normal
    LOW         = 4  # Logging, estadísticas


# ══════════════════════════════════════════════════
# ESTRUCTURA DE EVENTOS
# ══════════════════════════════════════════════════

@dataclass
class EventData:
    """
    Estructura de un evento en Jarvis.
    Todo evento tiene: tipo, origen, datos, prioridad y timestamp.

    Ejemplo:
        EventData(
            event_type=JarvisEvent.INTENT_RECOGNIZED,
            source="intent_recognizer",
            data={"intent": "play_music", "confidence": 0.95},
            priority=EventPriority.NORMAL
        )
    """
    event_type: JarvisEvent
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default="")
    error: Optional[Exception] = None

    def __post_init__(self):
        """Genera ID único si no se proporcionó"""
        if not self.event_id:
            self.event_id = f"{self.event_type.value}_{self.timestamp.timestamp():.0f}"

    def __lt__(self, other):
        """Permite ordenar por prioridad en PriorityQueue"""
        return self.priority.value < other.priority.value

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el evento a diccionario"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "source": self.source,
            "data": self.data,
            "priority": self.priority.name,
            "timestamp": self.timestamp.isoformat(),
            "has_error": self.error is not None
        }


# ══════════════════════════════════════════════════
# BUS DE EVENTOS
# ══════════════════════════════════════════════════

class EventBus:
    """
    Bus de eventos central de Jarvis.
    El sistema nervioso que conecta todos los módulos.

    Patrón: Publish-Subscribe
    - Módulos publican eventos sin saber quién escucha
    - Módulos se suscriben a eventos sin saber quién publica
    - El EventBus distribuye todo

    Uso básico:
        bus = EventBus()
        bus.start()

        # Suscribirse
        bus.subscribe(JarvisEvent.INTENT_RECOGNIZED, mi_funcion)

        # Publicar
        bus.publish(JarvisEvent.INTENT_RECOGNIZED, "intent_recognizer", {
            "intent": "play_music",
            "confidence": 0.95
        })
    """

    def __init__(self, max_queue_size: int = 1000):
        """
        Inicializa el EventBus.

        Args:
            max_queue_size: Máximo de eventos en cola simultáneamente
        """
        self.logger = JarvisLogger.get_logger("EventBus")
        self.event_logger = EventLogger()

        # Cola con prioridades (eventos críticos primero)
        self._queue: PriorityQueue = PriorityQueue(maxsize=max_queue_size)

        # Suscriptores: {JarvisEvent: [callbacks]}
        self._subscribers: Dict[JarvisEvent, List[Callable]] = defaultdict(list)

        # Suscriptores globales (reciben TODOS los eventos)
        self._global_subscribers: List[Callable] = []

        # Historial de eventos
        self._history: List[EventData] = []
        self._max_history: int = 500

        # Estadísticas por tipo de evento
        self._stats: Dict[str, int] = defaultdict(int)

        # Control de threading
        self._is_running: bool = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock: threading.Lock = threading.Lock()

        # Loop async para eventos async
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None

        self.logger.info("EventBus initialized")

    # ── Suscripción ──────────────────────────────

    def subscribe(self, event_type: JarvisEvent, callback: Callable) -> None:
        """
        Suscribe una función a un tipo de evento específico.

        Args:
            event_type: Tipo de evento a escuchar
            callback: Función que se ejecuta cuando llega el evento
                     Firma: callback(event: EventData) -> None

        Ejemplo:
            bus.subscribe(JarvisEvent.INTENT_RECOGNIZED, handle_intent)
        """
        with self._lock:
            self._subscribers[event_type].append(callback)
            self.logger.debug(f"Subscribed to {event_type.value}")

    def subscribe_many(self, event_types: List[JarvisEvent], callback: Callable) -> None:
        """
        Suscribe una función a múltiples tipos de eventos.

        Args:
            event_types: Lista de tipos de eventos
            callback: Función callback

        Ejemplo:
            bus.subscribe_many(
                [JarvisEvent.ACTION_COMPLETED, JarvisEvent.ACTION_FAILED],
                handle_action_result
            )
        """
        for event_type in event_types:
            self.subscribe(event_type, callback)

    def subscribe_all(self, callback: Callable) -> None:
        """
        Suscribe una función a TODOS los eventos.
        Útil para logging global o monitoreo.

        Args:
            callback: Función que recibe todos los eventos
        """
        with self._lock:
            self._global_subscribers.append(callback)
            self.logger.debug("Global subscriber added")

    def unsubscribe(self, event_type: JarvisEvent, callback: Callable) -> bool:
        """
        Desuscribe una función de un tipo de evento.

        Args:
            event_type: Tipo de evento
            callback: Función a desuscribir

        Returns:
            True si se encontró y removió, False si no estaba suscrita
        """
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                self.logger.debug(f"Unsubscribed from {event_type.value}")
                return True
            return False

    # ── Publicación ──────────────────────────────

    def publish(
        self,
        event_type: JarvisEvent,
        source: str,
        data: Dict[str, Any] = None,
        priority: EventPriority = EventPriority.NORMAL,
        error: Exception = None
    ) -> EventData:
        """
        Publica un evento en el bus.

        Args:
            event_type: Tipo de evento
            source: Quién publica el evento (ej: "intent_recognizer")
            data: Datos del evento
            priority: Prioridad del evento
            error: Excepción si es un evento de error

        Returns:
            El EventData creado

        Ejemplo:
            bus.publish(
                JarvisEvent.INTENT_RECOGNIZED,
                source="intent_recognizer",
                data={"intent": "play_music", "confidence": 0.95}
            )
        """
        event = EventData(
            event_type=event_type,
            source=source,
            data=data or {},
            priority=priority,
            error=error
        )

        try:
            # Usar prioridad numérica para PriorityQueue
            self._queue.put_nowait((priority.value, event))
            self.logger.debug(f"Event published: {event_type.value} from {source}")
            return event

        except Exception as e:
            self.logger.error(f"Failed to publish event {event_type.value}: {e}")
            return event

    def publish_error(
        self,
        source: str,
        error: Exception,
        data: Dict[str, Any] = None
    ) -> EventData:
        """
        Publica un evento de error (atajo conveniente).

        Args:
            source: Quién reporta el error
            error: La excepción ocurrida
            data: Datos adicionales del contexto

        Ejemplo:
            bus.publish_error("decision_engine", e, {"intent": "play_music"})
        """
        return self.publish(
            event_type=JarvisEvent.ERROR_OCCURRED,
            source=source,
            data={**(data or {}), "error_type": type(error).__name__, "error_msg": str(error)},
            priority=EventPriority.HIGH,
            error=error
        )

    # ── Control del bus ──────────────────────────

    def start(self) -> None:
        """
        Inicia el EventBus.
        Arranca el worker thread que procesa eventos.
        """
        if self._is_running:
            self.logger.warning("EventBus already running")
            return

        self._is_running = True
        self._worker_thread = threading.Thread(
            target=self._process_events,
            name="JarvisEventBus",
            daemon=True
        )
        self._worker_thread.start()
        self.logger.info("EventBus started")

    def stop(self) -> None:
        """
        Detiene el EventBus de forma segura.
        Espera a que se procesen los eventos pendientes.
        """
        self.logger.info("EventBus stopping...")
        self._is_running = False

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)

        self.logger.info("EventBus stopped")

    # ── Procesamiento interno ─────────────────────

    def _process_events(self) -> None:
        """
        Worker thread que procesa eventos de la cola.
        Se ejecuta continuamente hasta que se llame stop().
        """
        while self._is_running:
            try:
                # Esperar evento con timeout de 1 segundo
                _, event = self._queue.get(timeout=1)
                self._dispatch_event(event)
                self._queue.task_done()

            except Exception:
                # Timeout normal, continuar esperando
                continue

    def _dispatch_event(self, event: EventData) -> None:
        """
        Distribuye un evento a todos sus suscriptores.

        Args:
            event: El evento a distribuir
        """
        # Agregar al historial
        self._add_to_history(event)

        # Actualizar estadísticas
        self._stats[event.event_type.value] += 1

        # Log del evento
        self.event_logger.log_event(event.event_type.value, {
            "source": event.source,
            "data_keys": list(event.data.keys())
        })

        # Notificar suscriptores específicos
        with self._lock:
            callbacks = self._subscribers.get(event.event_type, []).copy()
            global_callbacks = self._global_subscribers.copy()

        for callback in callbacks:
            self._safe_call(callback, event)

        # Notificar suscriptores globales
        for callback in global_callbacks:
            self._safe_call(callback, event)

    def _safe_call(self, callback: Callable, event: EventData) -> None:
        """
        Ejecuta un callback de forma segura, capturando errores.

        Args:
            callback: Función a ejecutar
            event: Evento a pasar como argumento
        """
        try:
            callback(event)
        except Exception as e:
            self.logger.error(
                f"Error in callback {callback.__name__} "
                f"for event {event.event_type.value}: {e}"
            )

    def _add_to_history(self, event: EventData) -> None:
        """Agrega evento al historial, manteniendo tamaño máximo."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

    # ── Consultas ────────────────────────────────

    def get_history(
        self,
        limit: int = 20,
        event_type: Optional[JarvisEvent] = None
    ) -> List[EventData]:
        """
        Retorna el historial de eventos.

        Args:
            limit: Máximo de eventos a retornar
            event_type: Filtrar por tipo (None = todos)

        Returns:
            Lista de EventData ordenada por más reciente

        Ejemplo:
            # Últimos 10 eventos de decisión
            history = bus.get_history(10, JarvisEvent.DECISION_MADE)
        """
        history = self._history

        if event_type:
            history = [e for e in history if e.event_type == event_type]

        return history[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del EventBus.

        Returns:
            Diccionario con métricas del sistema de eventos

        Ejemplo de output:
            {
                "is_running": True,
                "queue_size": 3,
                "total_events": 150,
                "events_by_type": {"intent_recognized": 45, ...},
                "subscribers_count": 8
            }
        """
        return {
            "is_running": self._is_running,
            "queue_size": self._queue.qsize(),
            "total_events": len(self._history),
            "events_by_type": dict(self._stats),
            "subscribers_count": sum(
                len(v) for v in self._subscribers.values()
            ) + len(self._global_subscribers),
            "event_types_subscribed": [e.value for e in self._subscribers.keys()]
        }

    def clear_history(self) -> None:
        """Limpia el historial de eventos."""
        self._history.clear()
        self._stats.clear()
        self.logger.info("Event history cleared")

    def __repr__(self) -> str:
        return (
            f"EventBus("
            f"running={self._is_running}, "
            f"queue={self._queue.qsize()}, "
            f"history={len(self._history)})"
        )


# ══════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ══════════════════════════════════════════════════

_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Obtiene la instancia global del EventBus.
    Patrón Singleton — hay un solo bus en todo Jarvis.

    Returns:
        La instancia global del EventBus

    Ejemplo:
        bus = get_event_bus()
        bus.publish(JarvisEvent.SYSTEM_READY, "orchestrator", {})
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def init_event_bus(max_queue_size: int = 1000) -> EventBus:
    """
    Inicializa y arranca el EventBus global.
    Llamar una sola vez al arrancar Jarvis.

    Args:
        max_queue_size: Tamaño máximo de la cola

    Returns:
        El EventBus inicializado y corriendo

    Ejemplo:
        bus = init_event_bus()
        # Ahora todos los módulos pueden usar get_event_bus()
    """
    global _global_event_bus
    _global_event_bus = EventBus(max_queue_size=max_queue_size)
    _global_event_bus.start()
    return _global_event_bus
