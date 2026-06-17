"""
exceptions.py - Jerarquía de excepciones para Jarvis
Todos los errores siguen esta estructura para manejo consistente
"""

from typing import Optional
from enum import Enum


class ErrorSeverity(Enum):
    """Niveles de severidad de errores"""
    LOW = "low"          # No afecta funcionamiento
    MEDIUM = "medium"    # Afecta parcialmente
    HIGH = "high"        # Funcionalidad comprometida
    CRITICAL = "critical"  # Sistema no funciona


class JarvisBaseException(Exception):
    """
    Excepción base para todos los errores de Jarvis.
    
    Ejemplo:
        raise JarvisBaseException("Algo salió mal", severity=ErrorSeverity.HIGH)
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "JARVIS_ERROR",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[dict] = None
    ):
        """
        Inicializa la excepción.
        
        Args:
            message: Descripción del error
            error_code: Código único del error
            severity: Nivel de severidad
            context: Contexto adicional (diccionario)
        """
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.context = context or {}
        
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Formatea el mensaje de error"""
        base = f"[{self.error_code}] {self.message}"
        if self.context:
            context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base} | {context_str}"
        return base
    
    def to_dict(self) -> dict:
        """Convierte el error a diccionario para logging"""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'severity': self.severity.value,
            'context': self.context
        }


class ConfigException(JarvisBaseException):
    """
    Error en configuración.
    
    Ejemplo:
        raise ConfigException("API key no configurada")
    """
    
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            severity=ErrorSeverity.HIGH,
            context=context
        )


class AgentException(JarvisBaseException):
    """
    Error relacionado con agentes.
    
    Ejemplo:
        raise AgentException("Agent failed to initialize", context={"agent": "voice_agent"})
    """
    
    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        context: Optional[dict] = None
    ):
        if context is None:
            context = {}
        if agent_name:
            context['agent'] = agent_name
        
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )


class ToolException(JarvisBaseException):
    """
    Error en una herramienta/tool.
    
    Ejemplo:
        raise ToolException("Failed to execute command", context={"tool": "file_manager"})
    """
    
    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        context: Optional[dict] = None
    ):
        if context is None:
            context = {}
        if tool_name:
            context['tool'] = tool_name
        
        super().__init__(
            message=message,
            error_code="TOOL_ERROR",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )


class MemoryException(JarvisBaseException):
    """
    Error en el sistema de memoria.
    
    Ejemplo:
        raise MemoryException("Failed to save memory")
    """
    
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="MEMORY_ERROR",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )


class APIException(JarvisBaseException):
    """
    Error en llamadas a APIs externas.
    
    Ejemplo:
        raise APIException("Gemini API timeout", context={"api": "gemini", "timeout": 30})
    """
    
    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        status_code: Optional[int] = None,
        context: Optional[dict] = None
    ):
        if context is None:
            context = {}
        if api_name:
            context['api'] = api_name
        if status_code:
            context['status_code'] = status_code
        
        super().__init__(
            message=message,
            error_code="API_ERROR",
            severity=ErrorSeverity.HIGH if status_code and status_code >= 500 else ErrorSeverity.MEDIUM,
            context=context
        )


class VoiceException(JarvisBaseException):
    """
    Error en el sistema de voz (reconocimiento/síntesis).
    
    Ejemplo:
        raise VoiceException("Microphone not found")
    """
    
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="VOICE_ERROR",
            severity=ErrorSeverity.HIGH,
            context=context
        )


class TimeoutException(JarvisBaseException):
    """
    Error de timeout en operación.
    
    Ejemplo:
        raise TimeoutException("Operation took too long", context={"operation": "voice_recognition"})
    """
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        context: Optional[dict] = None
    ):
        if context is None:
            context = {}
        if timeout_seconds:
            context['timeout_seconds'] = timeout_seconds
        
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
