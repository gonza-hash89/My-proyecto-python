"""
Agent Base Class - Clase base para todos los agentes
Todos los agentes heredan de esta clase y deben implementar los métodos abstractos
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
import logging
from datetime import datetime


class Agent(ABC):
    """
    Clase base para todos los agentes de Jarvis.
    Define la interfaz que todos los agentes deben seguir.
    """

    def __init__(self, name: str, agent_type: str, config: Dict[str, Any] = None):
        """
        Inicializa un agente.

        Args:
            name: Nombre único del agente (ej: "voice_agent")
            agent_type: Tipo de agente (ej: "voice", "memory", "system")
            config: Diccionario de configuración específica del agente
        """
        self.name = name
        self.agent_type = agent_type
        self.config = config or {}
        self.is_active = True
        self.created_at = datetime.now()

        # Logger específico del agente
        self.logger = logging.getLogger(f"Jarvis.{self.name}")
        self.logger.info(f"Agent initialized: {self.name} (type: {self.agent_type})")

        # Bus de eventos (se asigna por el orquestador)
        self.event_bus = None

    @abstractmethod
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje/comando.
        TODOS los agentes deben implementar esto.

        Args:
            message: Diccionario con la información del mensaje
                    Ej: {
                        "type": "voice_input",
                        "data": "reproducir música",
                        "sender": "voice_agent"
                    }

        Returns:
            Diccionario con el resultado del procesamiento
            Ej: {
                "status": "success",
                "data": {"action": "play_music"},
                "next_agent": "system_agent"
            }
        """
        pass

    @abstractmethod
    def handle_event(self, event: Dict[str, Any]) -> None:
        """
        Maneja un evento que viene del bus.
        TODOS los agentes deben saber cómo reaccionar a eventos.

        Args:
            event: Evento que viene del bus de eventos
        """
        pass

    def send_message(self, message: Dict[str, Any]) -> None:
        """
        Envía un mensaje a través del bus de eventos a otros agentes.

        Args:
            message: Mensaje a enviar
        """
        if self.event_bus:
            message["sender"] = self.name
            message["timestamp"] = datetime.now().isoformat()
            self.logger.debug(f"Sending message: {message}")
            self.event_bus.publish(message)
        else:
            self.logger.warning("Event bus not connected!")

    def log_action(self, action: str, details: Dict[str, Any] = None) -> None:
        """
        Registra una acción del agente.

        Args:
            action: Descripción de la acción
            details: Detalles adicionales
        """
        log_data = {
            "agent": self.name,
            "action": action,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            log_data.update(details)

        self.logger.info(f"Action: {action} | Details: {details}")

    def stop(self) -> None:
        """Detiene el agente de forma segura."""
        self.is_active = False
        self.logger.info(f"Agent stopped: {self.name}")

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado actual del agente."""
        return {
            "name": self.name,
            "type": self.agent_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "config": self.config
        }

    def __repr__(self) -> str:
        return f"Agent(name={self.name}, type={self.agent_type}, active={self.is_active})"
