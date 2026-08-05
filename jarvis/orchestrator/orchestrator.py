"""Orquestador ligero para emitir y escuchar eventos.

Este archivo proporciona una implementación mínima en memoria que es
suficiente para pruebas y para integrarse con el módulo de memoria.
"""
from typing import Callable, Dict, List
from .events import Event
from .errors import ListenerError
import logging


logger = logging.getLogger("Jarvis.orchestrator")


class Orchestrator:
    def __init__(self):
        # listeners: event_name -> list of callables
        self._listeners: Dict[str, List[Callable[[Event], None]]] = {}

    def register_listener(self, event_name: str, callback: Callable[[Event], None]):
        self._listeners.setdefault(event_name, []).append(callback)
        logger.debug("Listener registrado para %s: %s", event_name, callback)

    def emit(self, event: Event):
        listeners = self._listeners.get(event.name, [])
        if not listeners:
            logger.debug("Ningún listener para evento: %s", event.name)
            return
        for cb in listeners:
            try:
                cb(event)
            except Exception as e:
                logger.exception("Error en listener para evento %s: %s", event.name, e)
                raise ListenerError(str(e))


# instancia global por conveniencia
default_orchestrator = Orchestrator()
