"""
Message Queue - Sistema de comunicación entre agentes
Implementa un Event Bus que permite que los agentes se comuniquen entre sí
"""

from typing import Dict, Any, Callable, List
from collections import defaultdict
from datetime import datetime
import logging
import threading
from queue import Queue


class MessageQueue:
    """
    Bus de eventos que permite la comunicación entre agentes.
    
    Funciona como un sistema publish-subscribe:
    - Los agentes "publican" mensajes
    - Los agentes se "suscriben" a ciertos tipos de mensajes
    - El bus distribuye los mensajes a los suscriptores
    """

    def __init__(self, max_queue_size: int = 1000):
        """
        Inicializa el Message Queue.

        Args:
            max_queue_size: Tamaño máximo de la cola de mensajes
        """
        self.logger = logging.getLogger("Jarvis.MessageQueue")
        
        # Cola interna de mensajes
        self.queue = Queue(maxsize=max_queue_size)
        
        # Suscriptores: {tipo_mensaje: [funciones_callback]}
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Historial de mensajes (para debugging)
        self.history: List[Dict[str, Any]] = []
        self.max_history = 100
        
        # Control de threads
        self.is_running = False
        self.worker_thread = None
        
        self.logger.info("MessageQueue initialized")

    def subscribe(self, message_type: str, callback: Callable) -> None:
        """
        Suscribe una función a un tipo de mensaje específico.

        Args:
            message_type: Tipo de mensaje (ej: "voice_input", "memory_query")
            callback: Función que se ejecutará cuando llegue ese mensaje
        
        Ejemplo:
            queue.subscribe("voice_input", my_agent.handle_event)
        """
        self.subscribers[message_type].append(callback)
        self.logger.debug(f"Subscriber added for '{message_type}'")

    def unsubscribe(self, message_type: str, callback: Callable) -> None:
        """
        Desuscribe una función de un tipo de mensaje.

        Args:
            message_type: Tipo de mensaje
            callback: Función a desuscribir
        """
        if callback in self.subscribers[message_type]:
            self.subscribers[message_type].remove(callback)
            self.logger.debug(f"Subscriber removed from '{message_type}'")

    def publish(self, message: Dict[str, Any]) -> None:
        """
        Publica un mensaje en el bus.
        El mensaje se distribuyará a todos los suscriptores.

        Args:
            message: Diccionario con el mensaje
                    Debe contener al menos:
                    {
                        "type": "voice_input",
                        "data": {...},
                        "sender": "voice_agent"
                    }
        """
        # Agregar metadata
        message["timestamp"] = datetime.now().isoformat()
        message["message_id"] = len(self.history)

        try:
            self.queue.put_nowait(message)
            self.logger.debug(f"Message published: {message.get('type')} from {message.get('sender')}")
        except Exception as e:
            self.logger.error(f"Error publishing message: {e}")

    def start(self) -> None:
        """Inicia el worker thread que procesa mensajes."""
        if self.is_running:
            self.logger.warning("MessageQueue already running")
            return

        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.worker_thread.start()
        self.logger.info("MessageQueue started")

    def stop(self) -> None:
        """Detiene el worker thread."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.logger.info("MessageQueue stopped")

    def _process_messages(self) -> None:
        """
        Worker que procesa mensajes de la cola de forma continua.
        Se ejecuta en un thread separado.
        """
        while self.is_running:
            try:
                # Espera a que haya un mensaje en la cola (timeout de 1 segundo)
                message = self.queue.get(timeout=1)

                # Agregar al historial
                self._add_to_history(message)

                # Obtener el tipo de mensaje
                message_type = message.get("type", "unknown")

                # Notificar a todos los suscriptores de este tipo
                if message_type in self.subscribers:
                    for callback in self.subscribers[message_type]:
                        try:
                            callback(message)
                        except Exception as e:
                            self.logger.error(f"Error in callback for '{message_type}': {e}")

                # También notificar a los suscriptores de "broadcast" (todos)
                if "*" in self.subscribers:
                    for callback in self.subscribers["*"]:
                        try:
                            callback(message)
                        except Exception as e:
                            self.logger.error(f"Error in broadcast callback: {e}")

                self.queue.task_done()

            except Exception:
                # timeout normal, continuar esperando
                continue

    def _add_to_history(self, message: Dict[str, Any]) -> None:
        """Agrega un mensaje al historial."""
        self.history.append(message)
        
        # Mantener tamaño máximo del historial
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna los últimos N mensajes del historial.

        Args:
            limit: Cantidad de mensajes a retornar

        Returns:
            Lista de mensajes
        """
        return self.history[-limit:]

    def clear_history(self) -> None:
        """Limpia el historial de mensajes."""
        self.history.clear()
        self.logger.info("Message history cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del MessageQueue."""
        return {
            "is_running": self.is_running,
            "queue_size": self.queue.qsize(),
            "total_messages": len(self.history),
            "subscribers_count": sum(len(v) for v in self.subscribers.values()),
            "message_types": list(self.subscribers.keys())
        }

    def __repr__(self) -> str:
        return f"MessageQueue(running={self.is_running}, queue_size={self.queue.qsize()})"
