"""Paquete de orquestador de Jarvis.

Contiene el sistema de eventos, el manejo de errores y el orquestador central.
"""

from .events import (
    Event,
    make_event,
    make_typed_event,
    EventBus,
    JarvisEvent,
    EventPriority,
    init_event_bus,
    get_event_bus,
)
from .errors import (
    OrchestratorError,
    EventNotFoundError,
    ListenerError,
    CircuitOpenError,
    AbortError,
    ErrorSeverity,
    RecoveryStrategy,
    ErrorContext,
    CircuitBreaker,
    ErrorHandler,
    init_error_handler,
    get_error_handler,
)
from .orchestrator import (
    Orchestrator,
    JarvisState,
    get_orchestrator,
)

__all__ = [
    # Eventos
    "Event",
    "make_event",
    "make_typed_event",
    "EventBus",
    "JarvisEvent",
    "EventPriority",
    "init_event_bus",
    "get_event_bus",
    # Errores
    "OrchestratorError",
    "EventNotFoundError",
    "ListenerError",
    "CircuitOpenError",
    "AbortError",
    "ErrorSeverity",
    "RecoveryStrategy",
    "ErrorContext",
    "CircuitBreaker",
    "ErrorHandler",
    "init_error_handler",
    "get_error_handler",
    # Orquestador
    "Orchestrator",
    "JarvisState",
    "get_orchestrator",
]
