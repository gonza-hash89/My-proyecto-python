"""
logger.py - Sistema de logging uniforme para Jarvis
Un único lugar donde TODOS los componentes loguean igual
"""

import logging
import logging.handlers
from typing import Optional
from pathlib import Path
from datetime import datetime


class JarvisFormatter(logging.Formatter):
    """Formateador personalizado para Jarvis con colores y contexto"""
    
    # Códigos ANSI para colores en consola
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Formatea el registro con color y contexto"""
        # Agregar color al nivel
        if hasattr(logging, 'disable') and not logging.disable(logging.NOTSET):
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
                )
        
        # Llamar al formateador padre
        return super().format(record)


class JarvisLogger:
    """
    Sistema centralizado de logging para Jarvis.
    
    Ejemplo de uso:
        logger = JarvisLogger.get_logger("voice_agent")
        logger.info("Agent started")
        logger.debug("Processing input")
        logger.error("Something went wrong")
    """
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def configure(
        cls,
        level: str = "INFO",
        log_file: str = "logs/jarvis.log",
        console_output: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """
        Configura el sistema de logging globalmente.
        
        Args:
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Ruta del archivo de log
            console_output: Si mostrar logs en consola
            max_bytes: Tamaño máximo del archivo antes de rotar
            backup_count: Cantidad de archivos de backup a mantener
        """
        if cls._configured:
            return
        
        # Crear directorio de logs si no existe
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Obtener nivel de logging
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Formato estándar para todos los loggers
        format_string = (
            "%(asctime)s | "
            "%(name)s | "
            "%(levelname)s | "
            "%(funcName)s:%(lineno)d | "
            "%(message)s"
        )
        
        # Configurar root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Handler para archivo (sin colores)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Handler para consola (con colores)
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = JarvisFormatter(format_string)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtiene un logger para un componente específico.
        
        Args:
            name: Nombre del componente (ej: "voice_agent", "orchestrator")
        
        Returns:
            Logger configurado para ese componente
        
        Ejemplo:
            logger = JarvisLogger.get_logger("my_agent")
            logger.info("Algo importante")
        """
        if name not in cls._loggers:
            logger = logging.getLogger(f"Jarvis.{name}")
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def reset(cls):
        """Reinicia la configuración de logging (útil para pruebas)"""
        cls._loggers.clear()
        cls._configured = False
        
        # Limpiar handlers del root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)


class AgentLogger:
    """
    Logger especializado para agentes con contexto automático.
    
    Ejemplo:
        agent_logger = AgentLogger(agent_name="voice_agent", agent_id="va_001")
        agent_logger.info("Started processing")  
        # Output: "voice_agent (va_001) | INFO | Started processing"
    """
    
    def __init__(self, agent_name: str, agent_id: Optional[str] = None):
        """
        Inicializa el logger del agente.
        
        Args:
            agent_name: Nombre del agente
            agent_id: ID único del agente (opcional)
        """
        self.agent_name = agent_name
        self.agent_id = agent_id or agent_name
        self.logger = JarvisLogger.get_logger(agent_name)
        self._context = {
            "agent": agent_name,
            "agent_id": self.agent_id
        }
    
    def _format_message(self, message: str, extra_context: dict = None) -> str:
        """Formatea el mensaje con contexto del agente"""
        context_str = f"[{self.agent_name}:{self.agent_id}]"
        if extra_context:
            context_items = " | ".join(f"{k}={v}" for k, v in extra_context.items())
            return f"{context_str} {message} | {context_items}"
        return f"{context_str} {message}"
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self.logger.debug(self._format_message(message, kwargs))
    
    def info(self, message: str, **kwargs):
        """Log de información"""
        self.logger.info(self._format_message(message, kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log de advertencia"""
        self.logger.warning(self._format_message(message, kwargs))
    
    def error(self, message: str, **kwargs):
        """Log de error"""
        self.logger.error(self._format_message(message, kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log crítico"""
        self.logger.critical(self._format_message(message, kwargs))


class PerformanceLogger:
    """
    Logger especializado para medir performance y tiempos.
    
    Ejemplo:
        with PerformanceLogger("process_input") as perf:
            # hacer algo
            pass
        # Output: "process_input completed in 0.234s"
    """
    
    def __init__(self, operation_name: str, logger: logging.Logger = None):
        """
        Inicializa el logger de performance.
        
        Args:
            operation_name: Nombre de la operación a medir
            logger: Logger a usar (por defecto, root logger)
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger("Jarvis.Performance")
        self.start_time = None
    
    def __enter__(self):
        """Inicia la medición"""
        self.start_time = datetime.now()
        self.logger.debug(f"⏱️ Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Finaliza la medición y loguea el tiempo"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f"✅ {self.operation_name} completed in {elapsed:.3f}s"
            )
        else:
            self.logger.error(
                f"❌ {self.operation_name} failed after {elapsed:.3f}s: {exc_val}"
            )
        
        return False  # No suprimir excepciones


class EventLogger:
    """
    Logger especializado para eventos del sistema.
    
    Ejemplo:
        event_logger = EventLogger()
        event_logger.log_event("agent_started", {"agent": "voice_agent"})
        event_logger.log_event("intent_recognized", {"intent": "play_music"})
    """
    
    def __init__(self):
        """Inicializa el logger de eventos"""
        self.logger = JarvisLogger.get_logger("Events")
    
    def log_event(self, event_type: str, data: dict = None):
        """
        Loguea un evento del sistema.
        
        Args:
            event_type: Tipo de evento (ej: "agent_started")
            data: Datos asociados al evento
        """
        data = data or {}
        timestamp = datetime.now().isoformat()
        
        message = f"EVENT: {event_type}"
        if data:
            data_str = " | ".join(f"{k}={v}" for k, v in data.items())
            message += f" | {data_str}"
        
        self.logger.info(message)
    
    def log_agent_lifecycle(self, agent_name: str, status: str, details: dict = None):
        """Loguea eventos del ciclo de vida de un agente"""
        self.log_event(
            f"agent_{status}",
            {"agent": agent_name, **(details or {})}
        )
    
    def log_message_flow(self, sender: str, receiver: str, message_type: str):
        """Loguea el flujo de mensajes entre agentes"""
        self.log_event(
            "message_flow",
            {"from": sender, "to": receiver, "type": message_type}
        )


# Inicializar logger por defecto
def init_logger(config=None):
    """
    Inicializa el sistema de logging con configuración.
    
    Args:
        config: Objeto de configuración (si None, usa valores por defecto)
    """
    if config is None:
        # Configuración por defecto
        JarvisLogger.configure(
            level="INFO",
            log_file="logs/jarvis.log",
            console_output=True
        )
    else:
        # Usar configuración proporcionada
        JarvisLogger.configure(
            level=config.logging.level,
            log_file=config.logging.file_path,
            console_output=config.logging.console_output,
            max_bytes=config.logging.max_file_size
        )
