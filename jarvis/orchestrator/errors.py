"""Errores personalizados para el orquestador."""


class OrchestratorError(Exception):
    """Error base del orquestador."""


class EventNotFoundError(OrchestratorError):
    """Evento no encontrado en registro."""


class ListenerError(OrchestratorError):
    """Error lanzado por un listener."""
