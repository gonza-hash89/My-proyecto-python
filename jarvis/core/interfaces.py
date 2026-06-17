"""
interfaces.py - Contratos (interfaces) que todo componente debe cumplir
Esto permite que agentes y herramientas sean intercambiables
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AgentStatus(Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"                    # Esperando
    INITIALIZING = "initializing"    # Arrancando
    PROCESSING = "processing"        # Procesando
    READY = "ready"                  # Listo
    ERROR = "error"                  # Error
    STOPPED = "stopped"              # Detenido


@dataclass
class AgentResponse:
    """
    Respuesta estándar de un agente.
    
    Atributos:
        success: Si la operación fue exitosa
        data: Datos de la respuesta
        message: Mensaje legible
        error: Información del error (si aplica)
        metadata: Información adicional (timing, etc)
    """
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AgentBase(ABC):
    """
    Interfaz base que todos los agentes DEBEN implementar.
    
    Ejemplo de uso:
        class VoiceAgent(AgentBase):
            def __init__(self):
                super().__init__("voice", "1.0.0")
            
            async def execute(self, command):
                # Implementación específica
                pass
    """
    
    def __init__(self, name: str, version: str):
        """
        Inicializa el agente.
        
        Args:
            name: Nombre único del agente
            version: Versión del agente (ej: "1.0.0")
        """
        self.name = name
        self.version = version
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_execution = None
    
    @abstractmethod
    async def initialize(self) -> AgentResponse:
        """
        Inicializa el agente.
        Llamado una sola vez al arrancar.
        
        Returns:
            AgentResponse con resultado de inicialización
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> AgentResponse:
        """
        Ejecuta la acción principal del agente.
        
        Args:
            **kwargs: Parámetros específicos del agente
        
        Returns:
            AgentResponse con resultado de ejecución
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> AgentResponse:
        """
        Limpia recursos y apaga el agente.
        
        Returns:
            AgentResponse confirmando apagado
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente"""
        return {
            'name': self.name,
            'version': self.version,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None
        }


class ToolBase(ABC):
    """
    Interfaz base para todas las herramientas.
    Las herramientas son funciones que los agentes pueden invocar.
    
    Ejemplo:
        class FileToolOpen(ToolBase):
            def __init__(self):
                super().__init__("file_open", "Abre un archivo")
            
            def execute(self, filepath: str):
                # Implementación
                pass
    """
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """
        Inicializa la herramienta.
        
        Args:
            name: Nombre único de la herramienta
            description: Descripción de qué hace
            version: Versión de la herramienta
        """
        self.name = name
        self.description = description
        self.version = version
        self.created_at = datetime.now()
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Ejecuta la herramienta.
        
        Args:
            **kwargs: Parámetros específicos de la herramienta
        
        Returns:
            Diccionario con resultado
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Retorna el esquema de parámetros de la herramienta.
        Útil para que los agentes sepan cómo invocarla.
        
        Returns:
            Esquema JSON Schema
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Información sobre la herramienta"""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'schema': self.get_schema()
        }


class MemoryBase(ABC):
    """
    Interfaz base para sistemas de memoria.
    Permite diferentes implementaciones (local, remota, hybrid, etc)
    
    Ejemplo:
        class LocalMemory(MemoryBase):
            def save(self, key, value):
                # Implementación
                pass
    """
    
    def __init__(self, name: str):
        """
        Inicializa la memoria.
        
        Args:
            name: Nombre de la memoria (ej: "short_term", "long_term")
        """
        self.name = name
        self.created_at = datetime.now()
    
    @abstractmethod
    async def save(self, key: str, value: Any, metadata: Dict = None) -> bool:
        """
        Guarda un valor en memoria.
        
        Args:
            key: Clave única
            value: Valor a guardar
            metadata: Información adicional (timestamps, tags, etc)
        
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    async def recall(self, key: str) -> Optional[Any]:
        """
        Recupera un valor de la memoria.
        
        Args:
            key: Clave a recuperar
        
        Returns:
            Valor si existe, None en caso contrario
        """
        pass
    
    @abstractmethod
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca en la memoria por contenido.
        
        Args:
            query: Término de búsqueda
        
        Returns:
            Lista de resultados
        """
        pass
    
    @abstractmethod
    async def forget(self, key: str) -> bool:
        """
        Elimina un valor de la memoria.
        
        Args:
            key: Clave a eliminar
        
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Limpia toda la memoria.
        
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas de la memoria.
        
        Returns:
            Diccionario con stats (tamaño, items, etc)
        """
        pass


class EventBase(ABC):
    """
    Interfaz base para el sistema de eventos.
    Los agentes se comunican publicando/escuchando eventos.
    
    Ejemplo:
        class IntentRecognizedEvent(EventBase):
            def __init__(self, intent: str, confidence: float):
                super().__init__("intent_recognized")
                self.intent = intent
                self.confidence = confidence
    """
    
    def __init__(self, event_type: str):
        """
        Inicializa el evento.
        
        Args:
            event_type: Tipo único del evento
        """
        self.event_type = event_type
        self.timestamp = datetime.now()
        self.source: Optional[str] = None  # Nombre del agente que lo genera
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el evento a diccionario.
        
        Returns:
            Diccionario con datos del evento
        """
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }


class EventBusBase(ABC):
    """
    Interfaz base para el bus de eventos.
    Permite que los agentes se comuniquen desacoplados.
    
    Ejemplo:
        bus = EventBus()
        await bus.subscribe('intent_recognized', my_handler)
        await bus.publish(MyEvent())
    """
    
    @abstractmethod
    async def publish(self, event: EventBase) -> bool:
        """
        Publica un evento.
        
        Args:
            event: Evento a publicar
        
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    async def subscribe(self, event_type: str, handler) -> str:
        """
        Se suscribe a un tipo de evento.
        
        Args:
            event_type: Tipo de evento a escuchar
            handler: Función async que maneja el evento
        
        Returns:
            ID de la suscripción (para desuscribirse)
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Se desuscribe de un evento.
        
        Args:
            subscription_id: ID de la suscripción
        
        Returns:
            True si fue exitoso
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Limpia todas las suscripciones.
        
        Returns:
            True si fue exitoso
        """
        pass
