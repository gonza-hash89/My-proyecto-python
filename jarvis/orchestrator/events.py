"""Eventos simples para el orquestador de Jarvis.

Archivo ligero con tipos de eventos y utilidades.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class Event:
    """Representa un evento en el sistema."""
    name: str
    payload: Dict[str, Any]
    timestamp: datetime = datetime.now()

    def __repr__(self) -> str:
        return f"Event(name={self.name}, payload={self.payload}, timestamp={self.timestamp.isoformat()})"


def make_event(name: str, payload: Dict[str, Any] | None = None) -> Event:
    return Event(name=name, payload=payload or {})
