"""
errors.py - Sistema de manejo de errores y recuperación de Jarvis

Resiliencia es parte de la arquitectura:
- Circuit Breaker: si una fuente falla repetidamente, deja de golpearla
- Reintentos automáticos con backoff exponencial
- Estrategias de recuperación (RETRY, FALLBACK, CLARIFY, SKIP, ABORT)
- Decoradores reutilizables (@with_error_handling, @with_retry)
- Integración con el EventBus (ERROR_OCCURRED / ERROR_CRITICAL)
- Singleton (get_error_handler / init_error_handler)

Filosofía: "Mejor lento y bien, que rápido y mal".
Jarvis nunca debe romper por un error recuperable: tiene un plan B.
"""

import functools
import logging
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional


# ==================== EXCEPCIONES DEL SISTEMA ====================

class OrchestratorError(Exception):
    """Error base del orquestador."""


class EventNotFoundError(OrchestratorError):
    """Evento no encontrado en registro."""


class ListenerError(OrchestratorError):
    """Error lanzado por un listener."""


class CircuitOpenError(OrchestratorError):
    """El circuit breaker está abierto: la fuente no está disponible."""


class AbortError(OrchestratorError):
    """La estrategia ABORT fue ejecutada: se aborta la operación."""


# ==================== ENUMS ====================

class ErrorSeverity(Enum):
    """Niveles de severidad de un error."""
    INFO = 1      # Informativo, no afecta el funcionamiento
    WARNING = 2   # Advertencia, funcionamiento degradado
    ERROR = 3     # Error, una operación falló
    CRITICAL = 4  # Crítico, el sistema puede detenerse


class RecoveryStrategy(Enum):
    """Estrategias de recuperación ante un error."""
    RETRY = "retry"          # Reintentar la operación con backoff
    FALLBACK = "fallback"    # Usar una alternativa
    CLARIFY = "clarify"      # Pedir clarificación al usuario
    SKIP = "skip"            # Omitir la operación (log y seguir)
    ABORT = "abort"          # Abortar la operación (elevar excepción)


class CircuitBreakerState(Enum):
    """Estados del circuit breaker."""
    CLOSED = "closed"          # Normal: las llamadas pasan
    OPEN = "open"              # Falló mucho: las llamadas se rechazan
    HALF_OPEN = "half_open"    # Probando recuperación


# ==================== CONTEXTO DE ERROR ====================

@dataclass
class ErrorContext:
    """Contexto completo de un error ocurrido en el sistema."""
    operation: str                       # Qué se estaba haciendo
    error_type: str                      # Tipo de excepción
    message: str                         # Mensaje del error
    severity: ErrorSeverity = ErrorSeverity.ERROR
    strategy: RecoveryStrategy = RecoveryStrategy.SKIP
    attempts: int = 0                    # Reintentos realizados
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para logging/serialización."""
        return {
            "operation": self.operation,
            "error_type": self.error_type,
            "message": self.message,
            "severity": self.severity.name,
            "strategy": self.strategy.name,
            "attempts": self.attempts,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


# ==================== CIRCUIT BREAKER ====================

class CircuitBreaker:
    """Protege fuentes de fallos repetidos.

    - CLOSED:  normal, las llamadas pasan
    - OPEN:    tras N fallos consecutivos, rechaza llamadas por un tiempo
    - HALF_OPEN: tras el tiempo de recuperación, deja pasar una llamada de prueba

    Ejemplo:
        breaker = CircuitBreaker("gemini_api")
        breaker.call(mi_funcion, ...)  # lanza CircuitOpenError si está abierto
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        """
        Args:
            name:             Nombre del recurso protegido
            failure_threshold: Fallos consecutivos antes de abrir
            recovery_timeout:  Segundos que permanece abierto antes de probar
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitBreakerState.CLOSED
        self._consecutive_failures = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.RLock()
        self.logger = logging.getLogger(f"Jarvis.CircuitBreaker.{name}")

    # ---------- Propiedades ----------

    @property
    def state(self) -> CircuitBreakerState:
        """Estado actual del breaker (evaluando half-open)."""
        with self._lock:
            if (
                self._state == CircuitBreakerState.OPEN
                and self._last_failure_time is not None
                and (time.monotonic() - self._last_failure_time) >= self.recovery_timeout
            ):
                self._state = CircuitBreakerState.HALF_OPEN
                self.logger.info("Circuit '%s' → HALF_OPEN (probando recuperación)", self.name)
            return self._state

    @property
    def is_available(self) -> bool:
        """True si las llamadas están permitidas."""
        return self.state != CircuitBreakerState.OPEN

    # ---------- Llamada protegida ----------

    def call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Ejecuta fn protegida por el breaker.

        Raises:
            CircuitOpenError: si el breaker está abierto
        """
        if not self.is_available:
            raise CircuitOpenError(
                f"Circuit '{self.name}' está abierto. "
                f"Se rechaza la llamada por {self.recovery_timeout}s."
            )

        try:
            result = fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    # ---------- Registro de resultados ----------

    def record_success(self) -> None:
        """Registra un éxito (resetea el contador de fallos)."""
        with self._lock:
            self._consecutive_failures = 0
            if self._state != CircuitBreakerState.CLOSED:
                self._state = CircuitBreakerState.CLOSED
                self.logger.info("Circuit '%s' → CLOSED (recuperado)", self.name)

    def record_failure(self) -> None:
        """Registra un fallo (puede abrir el circuito)."""
        with self._lock:
            self._consecutive_failures += 1
            self._last_failure_time = time.monotonic()
            if (
                self._consecutive_failures >= self.failure_threshold
                and self._state == CircuitBreakerState.CLOSED
            ):
                self._state = CircuitBreakerState.OPEN
                self.logger.warning(
                    "Circuit '%s' → OPEN (%d fallos consecutivos)",
                    self.name, self._consecutive_failures,
                )

    def reset(self) -> None:
        """Reinicia el breaker a estado CLOSED."""
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._consecutive_failures = 0
            self._last_failure_time = None

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del breaker."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "consecutive_failures": self._consecutive_failures,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout,
            }


# ==================== MANEJADOR DE ERRORES ====================

class ErrorHandler:
    """Centro de inteligencia de errores de Jarvis.

    Decide QUÉ hacer ante cada error según la estrategia:
    - RETRY:    reintenta con backoff exponencial
    - FALLBACK: ejecuta una alternativa
    - CLARIFY:  registra que hace falta aclaración del usuario
    - SKIP:     registra y continúa (por defecto)
    - ABORT:    eleva la excepción (operaciones que no deben continuar)

    Todos los errores se registran, se publican en el EventBus y
    se acumulan estadísticas por operación y tipo.
    """

    def __init__(self, event_bus: Optional[Any] = None):
        """
        Args:
            event_bus: Bus de eventos (opcional, se resuelve solo si None)
        """
        self.logger = logging.getLogger("Jarvis.ErrorHandler")
        self._event_bus = event_bus

        # Circuit breakers registrados: {nombre: CircuitBreaker}
        self._breakers: Dict[str, CircuitBreaker] = {}

        # Estadísticas
        self._total_errors = 0
        self._errors_by_operation: Counter = Counter()
        self._errors_by_type: Counter = Counter()
        self._errors_by_severity: Counter = Counter()
        self._lock = threading.RLock()

        self.logger.info("ErrorHandler initialized")

    # ---------- Acceso al bus ----------

    def _get_bus(self) -> Any:
        """Obtiene el EventBus (singleton si no fue inyectado)."""
        if self._event_bus is None:
            from orchestrator.events import get_event_bus
            self._event_bus = get_event_bus()
        return self._event_bus

    # ---------- Registro de errores ----------

    def handle(
        self,
        exception: Exception,
        operation: str = "unknown",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        strategy: RecoveryStrategy = RecoveryStrategy.SKIP,
        fallback: Optional[Callable[[], Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Maneja un error ya capturado.

        Args:
            exception:  La excepción ocurrida
            operation:  Operación que falló
            severity:   Severidad del error
            strategy:   Estrategia de recuperación
            fallback:   Alternativa a ejecutar si strategy == FALLBACK
            details:    Detalles adicionales

        Returns:
            Resultado del fallback si se usó FALLBACK, si no None.
            Con ABORT lanza la excepción original.
        """
        context = ErrorContext(
            operation=operation,
            error_type=type(exception).__name__,
            message=str(exception),
            severity=severity,
            strategy=strategy,
            details=details or {},
        )

        self._record(context)
        self._publish_error(exception, context)

        # Registrar según severidad
        level = {
            ErrorSeverity.INFO: self.logger.info,
            ErrorSeverity.WARNING: self.logger.warning,
            ErrorSeverity.ERROR: self.logger.error,
            ErrorSeverity.CRITICAL: self.logger.critical,
        }[severity]
        level("[%s] %s en '%s': %s", strategy.name, type(exception).__name__,
              operation, exception)

        # Aplicar estrategia
        if strategy == RecoveryStrategy.FALLBACK:
            if fallback is None:
                self.logger.warning("FALLBACK pedido sin fallback para '%s'", operation)
                return None
            try:
                result = fallback()
                self.logger.info("Fallback ejecutado para '%s'", operation)
                return result
            except Exception as fb_err:
                self.logger.error("Fallback también falló para '%s': %s", operation, fb_err)
                return None

        if strategy == RecoveryStrategy.ABORT:
            raise exception

        if strategy == RecoveryStrategy.RETRY:
            # Ya no se puede reintentar (la llamada ya falló).
            # Se registra y se comporta como SKIP para no colgar el sistema.
            self.logger.warning(
                "RETRY solicitado pero el error ya ocurrió en '%s'; usando SKIP", operation
            )

        if strategy == RecoveryStrategy.CLARIFY:
            self.logger.info(
                "CLARIFY: se necesita aclaración del usuario en '%s': %s", operation, exception
            )

        # SKIP (y demás): registrar y continuar
        return None

    # ---------- Ejecución con reintentos ----------

    def execute(
        self,
        fn: Callable,
        operation: str,
        *args: Any,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        retries: int = 2,
        delay: float = 0.5,
        **kwargs: Any,
    ) -> Any:
        """
        Ejecuta fn manejando errores y reintentos.

        Args:
            fn:        Función a ejecutar
            operation: Nombre de la operación
            retries:   Número de reintentos
            delay:     Retraso inicial (se duplica en cada intento)

        Returns:
            Resultado de fn, o None si se agotaron los intentos.
        """
        last_error: Optional[Exception] = None
        current_delay = delay

        for attempt in range(retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001
                last_error = e
                self.handle(
                    exception=e,
                    operation=operation,
                    severity=severity,
                    strategy=RecoveryStrategy.SKIP,
                    details={"attempt": attempt + 1, "total": retries + 1},
                )
                if attempt < retries:
                    time.sleep(current_delay)
                    current_delay *= 2  # backoff exponencial

        return None

    # ---------- Circuit breakers ----------

    def get_breaker(self, name: str, **kwargs: Any) -> CircuitBreaker:
        """Obtiene (o crea) un circuit breaker registrado."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, **kwargs)
            return self._breakers[name]

    # ---------- Decoradores ----------

    def with_error_handling(
        self,
        operation: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        strategy: RecoveryStrategy = RecoveryStrategy.SKIP,
        fallback: Optional[Callable[[], Any]] = None,
    ) -> Callable:
        """
        Decorador que envuelve una función con manejo de errores.

        Ejemplo:
            @error_handler.with_error_handling(operation="play_music")
            def play(self, song): ...
        """
        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                op = operation or fn.__name__
                try:
                    return fn(*args, **kwargs)
                except Exception as e:  # noqa: BLE001
                    return self.handle(
                        exception=e,
                        operation=op,
                        severity=severity,
                        strategy=strategy,
                        fallback=fallback,
                    )
            return wrapper
        return decorator

    def with_retry(
        self,
        operation: Optional[str] = None,
        retries: int = 2,
        delay: float = 0.5,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
    ) -> Callable:
        """
        Decorador que reintenta una función con backoff exponencial.

        Ejemplo:
            @error_handler.with_retry(operation="web_search", retries=3)
            def search(self, query): ...
        """
        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                op = operation or fn.__name__
                return self.execute(
                    fn, op, *args, severity=severity,
                    strategy=RecoveryStrategy.RETRY,
                    retries=retries, delay=delay, **kwargs,
                )
            return wrapper
        return decorator

    # ---------- Internos ----------

    def _record(self, context: ErrorContext) -> None:
        """Acumula el error en las estadísticas internas."""
        with self._lock:
            self._total_errors += 1
            self._errors_by_operation[context.operation] += 1
            self._errors_by_type[context.error_type] += 1
            self._errors_by_severity[context.severity.name] += 1

    def _publish_error(self, exception: Exception, context: ErrorContext) -> None:
        """Publica el error en el EventBus."""
        try:
            from orchestrator.events import (
                JarvisEvent,
                EventPriority,
                make_event,
            )
            event_name = (
                JarvisEvent.ERROR_CRITICAL.value
                if context.severity == ErrorSeverity.CRITICAL
                else JarvisEvent.ERROR_OCCURRED.value
            )
            priority = (
                EventPriority.CRITICAL
                if context.severity == ErrorSeverity.CRITICAL
                else EventPriority.HIGH
            )
            self._get_bus().publish(
                make_event(event_name, context.to_dict()),
                priority=priority,
            )
        except Exception:  # noqa: BLE001 - nunca romper por publicar un error
            self.logger.debug("No se pudo publicar el error en el EventBus")

    # ---------- Estadísticas ----------

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas globales del manejo de errores."""
        with self._lock:
            return {
                "total_errors": self._total_errors,
                "by_operation": dict(self._errors_by_operation),
                "by_type": dict(self._errors_by_type),
                "by_severity": dict(self._errors_by_severity),
                "circuit_breakers": {
                    name: breaker.get_stats()
                    for name, breaker in self._breakers.items()
                },
            }

    def reset_stats(self) -> None:
        """Reinicia las estadísticas de errores."""
        with self._lock:
            self._total_errors = 0
            self._errors_by_operation.clear()
            self._errors_by_type.clear()
            self._errors_by_severity.clear()

    def __repr__(self) -> str:
        return f"ErrorHandler(total_errors={self._total_errors})"


# ==================== SINGLETON ====================

_error_handler: Optional[ErrorHandler] = None


def init_error_handler() -> ErrorHandler:
    """
    (Re)inicializa el singleton del manejador de errores.

    Útil para pruebas (aislar entre tests) o reinicios.
    """
    global _error_handler
    _error_handler = ErrorHandler()
    return _error_handler


def get_error_handler() -> ErrorHandler:
    """Obtiene el singleton del manejador de errores (lo crea si no existe)."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


__all__ = [
    "OrchestratorError",
    "EventNotFoundError",
    "ListenerError",
    "CircuitOpenError",
    "AbortError",
    "ErrorSeverity",
    "RecoveryStrategy",
    "CircuitBreakerState",
    "ErrorContext",
    "CircuitBreaker",
    "ErrorHandler",
    "init_error_handler",
    "get_error_handler",
]
