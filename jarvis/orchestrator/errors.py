"""
errors.py - Sistema de manejo de errores de Jarvis
El sistema inmunológico que protege y recupera a Jarvis.

Filosofía:
- Un error no debe detener a Jarvis
- Cada error tiene una estrategia de recuperación
- Todo error queda registrado y trazable
- Degradación elegante: si algo falla, usar plan B

Estrategias disponibles:
- RETRY: Reintentar automáticamente
- FALLBACK: Usar alternativa más simple
- CLARIFY: Pedir aclaración al usuario
- SKIP: Saltar esta acción
- ABORT: Detener completamente (solo crítico)
"""

import time
import functools
import traceback
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type
from datetime import datetime

try:
    from .logger import JarvisLogger, AgentLogger
    from .exceptions import (
        JarvisBaseException, AgentException,
        NetworkException, APIException, APIKeyError,
        VoiceException, MemoryException
    )
    from ..orchestrator.events import get_event_bus, JarvisEvent, EventPriority
except ImportError:
    import logging
    class JarvisLogger:
        @classmethod
        def get_logger(cls, name):
            return logging.getLogger(f"Jarvis.{name}")
    class AgentLogger:
        def __init__(self, name, agent_id=None):
            self.logger = logging.getLogger(f"Jarvis.{name}")
        def __getattr__(self, name):
            return getattr(self.logger, name)
    JarvisBaseException = Exception
    AgentException = Exception
    NetworkException = Exception
    APIException = Exception
    APIKeyError = Exception
    VoiceException = Exception
    MemoryException = Exception


# ══════════════════════════════════════════════════
# ENUMERACIONES
# ══════════════════════════════════════════════════

class ErrorSeverity(Enum):
    """
    Niveles de severidad de errores.
    Determina qué tan urgente es la respuesta.

    INFO     → No es error, solo información
    WARNING  → Algo raro pero Jarvis continúa
    ERROR    → Fallo real, necesita recuperación
    CRITICAL → Fallo grave, puede detener Jarvis
    """
    INFO        = 1
    WARNING     = 2
    ERROR       = 3
    CRITICAL    = 4


class RecoveryStrategy(Enum):
    """
    Estrategias de recuperación disponibles.

    RETRY    → Reintentar la misma operación (errores transitorios)
    FALLBACK → Usar alternativa más simple (sin internet → local)
    CLARIFY  → Pedir aclaración al usuario (intent ambiguo)
    SKIP     → Saltar esta acción y continuar (no crítico)
    ABORT    → Detener completamente (error crítico)
    """
    RETRY       = "retry"
    FALLBACK    = "fallback"
    CLARIFY     = "clarify"
    SKIP        = "skip"
    ABORT       = "abort"


# ══════════════════════════════════════════════════
# ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════

@dataclass
class ErrorContext:
    """
    Contexto completo de un error ocurrido.
    Contiene todo lo necesario para diagnosticar y recuperarse.

    Ejemplo:
        ErrorContext(
            error=ConnectionError("Sin internet"),
            source="web_agent",
            severity=ErrorSeverity.ERROR,
            strategy=RecoveryStrategy.FALLBACK,
            context={"query": "noticias de hoy"}
        )
    """
    error: Exception
    source: str
    severity: ErrorSeverity
    strategy: RecoveryStrategy
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    resolved: bool = False
    resolution: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el contexto para logging y eventos"""
        return {
            "error_type": type(self.error).__name__,
            "error_msg": str(self.error),
            "source": self.source,
            "severity": self.severity.name,
            "strategy": self.strategy.value,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "context": self.context
        }


@dataclass
class RetryConfig:
    """
    Configuración para reintentos automáticos.

    Ejemplo:
        RetryConfig(max_retries=3, delay=1.0, backoff=2.0)
        → Intenta 3 veces, espera 1s, 2s, 4s entre intentos
    """
    max_retries: int = 3
    delay: float = 1.0         # Segundos entre reintentos
    backoff: float = 2.0       # Multiplicador de delay (exponencial)
    max_delay: float = 30.0    # Máximo delay entre reintentos


# ══════════════════════════════════════════════════
# MANEJADOR DE ERRORES
# ══════════════════════════════════════════════════

class ErrorHandler:
    """
    Manejador de errores inteligente de Jarvis.

    Responsabilidades:
    - Detectar el tipo y severidad de cada error
    - Elegir la estrategia de recuperación correcta
    - Ejecutar la recuperación
    - Registrar todo para análisis
    - Publicar eventos de error al EventBus

    Uso:
        handler = ErrorHandler()

        try:
            resultado = operacion_riesgosa()
        except Exception as e:
            contexto = handler.handle(e, source="mi_agente")
            if not contexto.resolved:
                # manejar fallo
    """

    def __init__(self, retry_config: RetryConfig = None):
        """
        Inicializa el manejador de errores.

        Args:
            retry_config: Configuración de reintentos (usa defaults si None)
        """
        self.logger = JarvisLogger.get_logger("ErrorHandler")
        self.retry_config = retry_config or RetryConfig()

        # Historial de errores
        self._error_history: List[ErrorContext] = []
        self._max_history: int = 200

        # Contadores por tipo de error
        self._error_counts: Dict[str, int] = {}

        # Circuit breaker: fuentes con demasiados errores
        self._circuit_breakers: Dict[str, int] = {}
        self._circuit_threshold: int = 5

        self.logger.info("ErrorHandler initialized")

    # ── Manejo principal ─────────────────────────

    def handle(
        self,
        error: Exception,
        source: str,
        context: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        Punto de entrada principal para manejar un error.

        Determina severidad, elige estrategia y registra todo.

        Args:
            error: La excepción ocurrida
            source: Quién reporta el error (ej: "web_agent")
            context: Datos adicionales del contexto

        Returns:
            ErrorContext con toda la información y resolución

        Ejemplo:
            try:
                resultado = gemini.query(prompt)
            except Exception as e:
                ctx = handler.handle(e, "dialog_agent", {"prompt": prompt})
        """
        severity = self.determine_severity(error)
        strategy = self.determine_strategy(error, severity)

        error_ctx = ErrorContext(
            error=error,
            source=source,
            severity=severity,
            strategy=strategy,
            context=context or {}
        )

        # Registrar error
        self._register_error(error_ctx)

        # Log según severidad
        self._log_error(error_ctx)

        # Publicar evento si el bus está disponible
        self._publish_error_event(error_ctx)

        # Incrementar circuit breaker
        self._circuit_breakers[source] = self._circuit_breakers.get(source, 0) + 1

        return error_ctx

    def handle_intent_error(
        self,
        error: Exception,
        user_input: str = "",
        context: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        Maneja errores específicos del reconocedor de intenciones.

        Estrategia típica:
        - Error de API → FALLBACK a reconocimiento local
        - Sin internet → FALLBACK
        - Intent ambiguo → CLARIFY

        Args:
            error: La excepción
            user_input: Lo que dijo el usuario
            context: Contexto adicional

        Returns:
            ErrorContext con estrategia específica
        """
        ctx = context or {}
        ctx["user_input"] = user_input

        error_ctx = self.handle(error, "intent_recognizer", ctx)

        # Ajuste específico para intenciones
        if isinstance(error, (NetworkException, APIException)):
            error_ctx.strategy = RecoveryStrategy.FALLBACK
            error_ctx.resolution = "Usando reconocimiento local sin API"
        elif "ambiguous" in str(error).lower():
            error_ctx.strategy = RecoveryStrategy.CLARIFY
            error_ctx.resolution = "Pidiendo aclaración al usuario"

        return error_ctx

    def handle_decision_error(
        self,
        error: Exception,
        intent_name: str = "",
        context: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        Maneja errores del motor de decisiones.

        Estrategia típica:
        - No hay agente → FALLBACK al agente de diálogo
        - Conflicto → usar mayor prioridad
        - Timeout → RETRY una vez, luego SKIP

        Args:
            error: La excepción
            intent_name: Nombre de la intención que falló
            context: Contexto adicional

        Returns:
            ErrorContext con estrategia específica
        """
        ctx = context or {}
        ctx["intent"] = intent_name

        error_ctx = self.handle(error, "decision_engine", ctx)

        # Fallback al agente de diálogo si no hay agente disponible
        if "no agent" in str(error).lower() or "not found" in str(error).lower():
            error_ctx.strategy = RecoveryStrategy.FALLBACK
            error_ctx.resolution = "Usando dialog_agent como fallback"

        return error_ctx

    def handle_action_error(
        self,
        error: Exception,
        agent_name: str = "",
        action: str = "",
        context: Dict[str, Any] = None
    ) -> ErrorContext:
        """
        Maneja errores durante la ejecución de acciones.

        Estrategia típica:
        - Error transitorio → RETRY
        - Permiso denegado → SKIP con aviso
        - Error de red → FALLBACK

        Args:
            error: La excepción
            agent_name: Agente que falló
            action: Acción que se intentaba ejecutar
            context: Contexto adicional

        Returns:
            ErrorContext con estrategia específica
        """
        ctx = context or {}
        ctx["agent"] = agent_name
        ctx["action"] = action

        error_ctx = self.handle(error, f"action_{agent_name}", ctx)

        # Errores de voz son recuperables
        if isinstance(error, VoiceException):
            error_ctx.strategy = RecoveryStrategy.RETRY
            error_ctx.resolution = "Reintentando síntesis de voz"

        # Errores de memoria son skip-able
        elif isinstance(error, MemoryException):
            error_ctx.strategy = RecoveryStrategy.SKIP
            error_ctx.resolution = "Continuando sin guardar en memoria"

        return error_ctx

    # ── Determinación ────────────────────────────

    def determine_severity(self, error: Exception) -> ErrorSeverity:
        """
        Determina qué tan grave es un error.

        Reglas:
        - APIKeyError → CRITICAL (sin clave, sin cerebro)
        - NetworkException → ERROR (recuperable)
        - VoiceException → WARNING (no crítico)
        - ValueError → WARNING (input inválido)
        - Exception genérica → ERROR

        Args:
            error: La excepción a clasificar

        Returns:
            Nivel de severidad
        """
        # Errores críticos — detienen o degradan mucho a Jarvis
        if isinstance(error, (APIKeyError, SystemExit, MemoryError)):
            return ErrorSeverity.CRITICAL

        # Errores graves — necesitan recuperación activa
        if isinstance(error, (APIException, NetworkException, AgentException)):
            return ErrorSeverity.ERROR

        # Errores de módulos de entrada/salida — recuperables
        if isinstance(error, (VoiceException, MemoryException)):
            return ErrorSeverity.WARNING

        # Errores de validación — informativos
        if isinstance(error, (ValueError, TypeError, KeyError)):
            return ErrorSeverity.WARNING

        # Default: error genérico
        return ErrorSeverity.ERROR

    def determine_strategy(
        self,
        error: Exception,
        severity: ErrorSeverity
    ) -> RecoveryStrategy:
        """
        Determina la mejor estrategia de recuperación.

        Lógica:
        - CRITICAL → ABORT (no hay recuperación segura)
        - NetworkException → FALLBACK (usar modo offline)
        - APIException → RETRY (puede ser transitorio)
        - VoiceException → RETRY (puede ser problema de mic)
        - WARNING genérico → SKIP
        - ERROR genérico → RETRY

        Args:
            error: La excepción
            severity: Severidad ya determinada

        Returns:
            Estrategia de recuperación recomendada
        """
        # Crítico → abortar
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.ABORT

        # Sin internet → fallback a modo local
        if isinstance(error, NetworkException):
            return RecoveryStrategy.FALLBACK

        # Error de API → reintentar (puede ser temporal)
        if isinstance(error, APIException):
            return RecoveryStrategy.RETRY

        # Error de voz → reintentar
        if isinstance(error, VoiceException):
            return RecoveryStrategy.RETRY

        # Error de memoria → skip (no es crítico)
        if isinstance(error, MemoryException):
            return RecoveryStrategy.SKIP

        # Warning genérico → skip
        if severity == ErrorSeverity.WARNING:
            return RecoveryStrategy.SKIP

        # Error genérico → reintentar
        return RecoveryStrategy.RETRY

    # ── Recuperación ─────────────────────────────

    def with_retry(
        self,
        func: Callable,
        *args,
        source: str = "unknown",
        config: RetryConfig = None,
        **kwargs
    ) -> Any:
        """
        Ejecuta una función con reintentos automáticos.

        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales para func
            source: Nombre del módulo que llama
            config: Configuración de reintentos (usa default si None)
            **kwargs: Argumentos keyword para func

        Returns:
            Resultado de func si tuvo éxito

        Raises:
            Exception: El último error si todos los reintentos fallan

        Ejemplo:
            resultado = handler.with_retry(
                gemini.query,
                prompt,
                source="dialog_agent",
                config=RetryConfig(max_retries=3, delay=2.0)
            )
        """
        cfg = config or self.retry_config
        last_error = None
        delay = cfg.delay

        for attempt in range(cfg.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                last_error = e

                if attempt < cfg.max_retries:
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{cfg.max_retries} failed "
                        f"for {source}: {e}. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * cfg.backoff, cfg.max_delay)
                else:
                    self.logger.error(
                        f"All {cfg.max_retries} retries failed for {source}: {e}"
                    )

        raise last_error

    def is_circuit_open(self, source: str) -> bool:
        """
        Verifica si el circuit breaker está abierto para una fuente.
        Si una fuente tiene demasiados errores, el circuit se abre
        y se deja de intentar usarla temporalmente.

        Args:
            source: Nombre del módulo o agente

        Returns:
            True si el circuit está abierto (demasiados errores)

        Ejemplo:
            if not handler.is_circuit_open("web_agent"):
                resultado = web_agent.search(query)
        """
        count = self._circuit_breakers.get(source, 0)
        is_open = count >= self._circuit_threshold

        if is_open:
            self.logger.warning(
                f"Circuit breaker OPEN for {source} "
                f"({count} errors >= threshold {self._circuit_threshold})"
            )

        return is_open

    def reset_circuit(self, source: str) -> None:
        """
        Resetea el circuit breaker de una fuente.
        Llamar cuando la fuente se recupera.

        Args:
            source: Nombre del módulo o agente
        """
        if source in self._circuit_breakers:
            del self._circuit_breakers[source]
            self.logger.info(f"Circuit breaker reset for {source}")

    # ── Internos ─────────────────────────────────

    def _register_error(self, error_ctx: ErrorContext) -> None:
        """Registra el error en el historial y contadores."""
        self._error_history.append(error_ctx)

        # Mantener tamaño máximo
        if len(self._error_history) > self._max_history:
            self._error_history.pop(0)

        # Actualizar contadores
        error_type = type(error_ctx.error).__name__
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def _log_error(self, error_ctx: ErrorContext) -> None:
        """Loguea el error según su severidad."""
        msg = (
            f"[{error_ctx.severity.name}] {type(error_ctx.error).__name__} "
            f"in {error_ctx.source}: {error_ctx.error} "
            f"→ Strategy: {error_ctx.strategy.value}"
        )

        if error_ctx.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(msg)
            self.logger.critical(traceback.format_exc())
        elif error_ctx.severity == ErrorSeverity.ERROR:
            self.logger.error(msg)
        elif error_ctx.severity == ErrorSeverity.WARNING:
            self.logger.warning(msg)
        else:
            self.logger.info(msg)

    def _publish_error_event(self, error_ctx: ErrorContext) -> None:
        """Publica el error al EventBus si está disponible."""
        try:
            bus = get_event_bus()
            if bus and bus._is_running:
                priority = (
                    EventPriority.CRITICAL
                    if error_ctx.severity == ErrorSeverity.CRITICAL
                    else EventPriority.HIGH
                )
                bus.publish(
                    JarvisEvent.ERROR_OCCURRED,
                    source=error_ctx.source,
                    data=error_ctx.to_dict(),
                    priority=priority,
                    error=error_ctx.error
                )
        except Exception:
            pass  # No queremos que el manejo de errores genere más errores

    # ── Consultas ────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas completas del sistema de errores.

        Returns:
            Diccionario con métricas de errores

        Ejemplo de output:
            {
                "total_errors": 15,
                "errors_by_type": {"ConnectionError": 5, ...},
                "errors_by_severity": {"ERROR": 10, ...},
                "circuit_breakers": {"web_agent": 3},
                "resolved": 12,
                "unresolved": 3
            }
        """
        severity_counts = {}
        for ctx in self._error_history:
            sev = ctx.severity.name
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "total_errors": len(self._error_history),
            "errors_by_type": dict(self._error_counts),
            "errors_by_severity": severity_counts,
            "circuit_breakers": dict(self._circuit_breakers),
            "resolved": sum(1 for e in self._error_history if e.resolved),
            "unresolved": sum(1 for e in self._error_history if not e.resolved),
            "circuit_threshold": self._circuit_threshold
        }

    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna los errores más recientes.

        Args:
            limit: Máximo de errores a retornar

        Returns:
            Lista de errores serializados
        """
        return [e.to_dict() for e in self._error_history[-limit:]]

    def __repr__(self) -> str:
        return (
            f"ErrorHandler("
            f"errors={len(self._error_history)}, "
            f"circuit_breakers={len(self._circuit_breakers)})"
        )


# ══════════════════════════════════════════════════
# DECORADORES ÚTILES
# ══════════════════════════════════════════════════

def with_error_handling(source: str, strategy: RecoveryStrategy = RecoveryStrategy.RETRY):
    """
    Decorador que agrega manejo de errores automático a una función.

    Args:
        source: Nombre del módulo (para logging)
        strategy: Estrategia de recuperación por defecto

    Uso:
        @with_error_handling("web_agent")
        def buscar_en_internet(query: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx = handler.handle(e, source)
                ctx.strategy = strategy
                if strategy == RecoveryStrategy.ABORT:
                    raise
                return None
        return wrapper
    return decorator


def with_retry(max_retries: int = 3, delay: float = 1.0, source: str = "unknown"):
    """
    Decorador que agrega reintentos automáticos a una función.

    Args:
        max_retries: Número máximo de reintentos
        delay: Segundos entre reintentos
        source: Nombre del módulo (para logging)

    Uso:
        @with_retry(max_retries=3, delay=2.0, source="gemini_client")
        def llamar_gemini(prompt: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_error_handler()
            config = RetryConfig(max_retries=max_retries, delay=delay)
            return handler.with_retry(func, *args, source=source, config=config, **kwargs)
        return wrapper
    return decorator


# ══════════════════════════════════════════════════
# INSTANCIA GLOBAL
# ══════════════════════════════════════════════════

_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Obtiene la instancia global del ErrorHandler.
    Patrón Singleton — hay un solo handler en todo Jarvis.

    Returns:
        La instancia global del ErrorHandler

    Ejemplo:
        handler = get_error_handler()
        ctx = handler.handle(e, "mi_agente")
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler
