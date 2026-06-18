"""
memory.py - Sistema de Memoria de Jarvis

Jarvis tiene DOS tipos de memoria:
1. SHORT TERM: Conversación actual (RAM rápido, se pierde al apagar)
2. LONG TERM: Todo lo que pasó antes (SQLite persistente)

MemoryManager coordina ambas y permite buscar, guardar y olvidar.

MÉTODOS DE BÚSQUEDA (IMPORTANTE):
- recall(key)    → Búsqueda EXACTA por clave (recall("user_name"))
- search(query)  → Búsqueda LIBRE en lenguaje natural (search("¿qué música me gusta?"))
"""

import sqlite3
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
from collections import deque


@dataclass
class MemoryItem:
    """Un item en memoria"""
    key: str
    value: Any
    importance: str  # "low", "normal", "high"
    timestamp: datetime
    metadata: Dict[str, Any]
    source: str  # "short_term" o "long_term"


@dataclass
class UserPreference:
    """Preferencia del usuario"""
    key: str
    value: str
    last_updated: datetime


@dataclass
class Entity:
    """Entidad extraída (persona, lugar, etc)"""
    entity_type: str
    entity_value: str
    mentions: int
    last_seen: datetime


class ShortTermMemory:
    """
    Memoria a corto plazo (RAM).
    
    Guarda la conversación actual. Se pierde al apagar.
    Rápida, pero limitada (máx 100 items).
    """
    
    def __init__(self, max_items: int = 100):
        """
        Inicializa memoria corto plazo.
        
        Args:
            max_items: Máximo número de items (después olvida el más viejo)
        """
        self.max_items = max_items
        self.items: deque = deque(maxlen=max_items)
        self.context: Dict[str, Any] = {}  # contexto actual (ubicación, actividad, etc)
    
    def save(self, key: str, value: Any, metadata: Dict = None):
        """
        Guarda un item en memoria corto plazo.
        
        Args:
            key: Clave única
            value: Valor
            metadata: Info adicional
        """
        item = MemoryItem(
            key=key,
            value=value,
            importance="normal",
            timestamp=datetime.now(),
            metadata=metadata or {},
            source="short_term"
        )
        self.items.append(item)
    
    def recall(self, key: str) -> Optional[MemoryItem]:
        """Recupera un item por clave exacta"""
        for item in self.items:
            if item.key == key:
                return item
        return None
    
    def recall_last(self, n: int = 5) -> List[MemoryItem]:
        """Retorna los últimos N items (conversación reciente)"""
        return list(self.items)[-n:]
    
    def set_context(self, context_key: str, context_value: Any):
        """Establece contexto actual (ubicación, actividad, etc)"""
        self.context[context_key] = context_value
    
    def get_context(self, context_key: str = None) -> Any:
        """Obtiene contexto actual"""
        if context_key:
            return self.context.get(context_key)
        return self.context
    
    def clear(self):
        """Limpia toda la memoria corto plazo"""
        self.items.clear()
        self.context.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas"""
        return {
            "name": "short_term",
            "total_items": len(self.items),
            "max_items": self.max_items,
            "context_keys": list(self.context.keys()),
            "oldest_entry": self.items[0].timestamp.isoformat() if self.items else None,
            "newest_entry": self.items[-1].timestamp.isoformat() if self.items else None
        }


class LongTermMemory:
    """
    Memoria a largo plazo (SQLite).
    
    Guarda todo persistentemente. Lenta pero confiable.
    Se queda en disco incluso después de apagar.
    """
    
    def __init__(self, db_path: str = "data/jarvis_memory.db"):
        """
        Inicializa memoria largo plazo.
        
        Args:
            db_path: Ruta de la base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()
    
    def _initialize_db(self):
        """Crea tablas si no existen"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabla de conversaciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_message TEXT,
                    agent_response TEXT,
                    intent TEXT,
                    importance TEXT DEFAULT 'normal',
                    tags TEXT
                )
            """)
            
            # Tabla de preferencias del usuario
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preference_key TEXT UNIQUE,
                    preference_value TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de entidades extraídas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT,
                    entity_value TEXT UNIQUE,
                    mentions INTEGER DEFAULT 1,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de memorias generales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    metadata TEXT,
                    importance TEXT DEFAULT 'normal',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    async def save(self, key: str, value: Any, metadata: Dict = None, importance: str = "normal"):
        """
        Guarda un item en memoria largo plazo (SQLite).
        
        Args:
            key: Clave única
            value: Valor (se serializa a JSON)
            metadata: Información adicional
            importance: "low", "normal", "high"
        """
        # Ejecutar en thread para no bloquear
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._save_sync,
            key,
            value,
            metadata,
            importance
        )
    
    def _save_sync(self, key: str, value: Any, metadata: Dict = None, importance: str = "normal"):
        """Versión síncrona de save (para usar con executor)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Serializar value y metadata a JSON
            value_json = json.dumps(value, default=str)
            metadata_json = json.dumps(metadata or {})
            
            # INSERT OR REPLACE para actualizar si existe
            cursor.execute("""
                INSERT OR REPLACE INTO memories (key, value, metadata, importance, accessed_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value_json, metadata_json, importance))
            
            conn.commit()
    
    async def recall(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Recupera un item por CLAVE EXACTA.
        
        Args:
            key: Clave exacta a recuperar
        
        Returns:
            El item si existe, None en caso contrario
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._recall_sync, key)
    
    def _recall_sync(self, key: str) -> Optional[Dict[str, Any]]:
        """Versión síncrona de recall"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key, value, metadata, importance, created_at, accessed_at
                FROM memories
                WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Actualizar accessed_at
            cursor.execute("""
                UPDATE memories SET accessed_at = CURRENT_TIMESTAMP WHERE key = ?
            """, (key,))
            conn.commit()
            
            return {
                "key": row[0],
                "value": json.loads(row[1]),
                "metadata": json.loads(row[2]),
                "importance": row[3],
                "created_at": row[4],
                "accessed_at": row[5]
            }
    
    async def save_conversation(self, user_message: str, agent_response: str, intent: str = None, importance: str = "normal"):
        """
        Guarda una conversación.
        
        Args:
            user_message: Lo que dijo el usuario
            agent_response: La respuesta de Jarvis
            intent: La intención detectada
            importance: Importancia de la conversación
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._save_conversation_sync,
            user_message,
            agent_response,
            intent,
            importance
        )
    
    def _save_conversation_sync(self, user_message: str, agent_response: str, intent: str = None, importance: str = "normal"):
        """Versión síncrona"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (user_message, agent_response, intent, importance)
                VALUES (?, ?, ?, ?)
            """, (user_message, agent_response, intent, importance))
            conn.commit()
    
    async def search_conversations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca conversaciones por similitud de texto.
        
        ⚠️ Búsqueda simple por LIKE. 
        Después podemos agregar búsqueda semántica con embeddings.
        
        Args:
            query: Término de búsqueda
            limit: Máximo de resultados
        
        Returns:
            Lista de conversaciones relevantes
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._search_conversations_sync,
            query,
            limit
        )
    
    def _search_conversations_sync(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Versión síncrona"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Búsqueda por coincidencia de texto (LIKE)
            cursor.execute("""
                SELECT timestamp, user_message, agent_response, intent
                FROM conversations
                WHERE user_message LIKE ? OR agent_response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "timestamp": row[0],
                    "user_message": row[1],
                    "agent_response": row[2],
                    "intent": row[3]
                })
            
            return results
    
    async def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca en memorias generales por coincidencia de texto.
        Complementa a search_conversations() que ya tenías.
        
        Args:
            query: Término de búsqueda en lenguaje natural
            limit: Máximo de resultados
        
        Returns:
            Lista de memorias relevantes ordenadas por más recientes
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._search_memories_sync,
            query,
            limit
        )
    
    def _search_memories_sync(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Versión síncrona de search_memories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key, value, metadata, importance, created_at
                FROM memories
                WHERE key LIKE ? OR value LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "key": row[0],
                    "value": json.loads(row[1]),
                    "metadata": json.loads(row[2]),
                    "importance": row[3],
                    "created_at": row[4]
                })
            
            return results
    
    async def save_preference(self, key: str, value: str):
        """
        Guarda una preferencia del usuario.
        
        Args:
            key: Tipo de preferencia (ej: "favorite_genre")
            value: Valor (ej: "rock")
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_preference_sync, key, value)
    
    def _save_preference_sync(self, key: str, value: str):
        """Versión síncrona"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_profile (preference_key, preference_value, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            conn.commit()
    
    async def get_user_profile(self) -> Dict[str, str]:
        """
        Retorna el perfil completo del usuario.
        
        Returns:
            Diccionario con todas las preferencias guardadas
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_user_profile_sync)
    
    def _get_user_profile_sync(self) -> Dict[str, str]:
        """Versión síncrona"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT preference_key, preference_value FROM user_profile")
            
            profile = {}
            for row in cursor.fetchall():
                profile[row[0]] = row[1]
            
            return profile
    
    async def save_entity(self, entity_type: str, entity_value: str):
        """
        Guarda una entidad extraída (persona, lugar, etc).
        
        ⚠️ LIMITACIÓN CONOCIDA: Si la misma persona aparece como
        "person" y luego como "place" (error de Gemini), el conflicto
        solo verifica entity_value, no la combinación tipo+valor.
        
        TODO: Agregar composite unique constraint (type + value)
        
        Args:
            entity_type: Tipo de entidad ("person", "place", "date", etc)
            entity_value: Valor de la entidad
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_entity_sync, entity_type, entity_value)
    
    def _save_entity_sync(self, entity_type: str, entity_value: str):
        """Versión síncrona"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Si existe, incrementar mentions
            cursor.execute("""
                INSERT INTO entities (entity_type, entity_value, mentions)
                VALUES (?, ?, 1)
                ON CONFLICT(entity_value) DO UPDATE
                SET mentions = mentions + 1, last_seen = CURRENT_TIMESTAMP
            """, (entity_type, entity_value))
            
            conn.commit()
    
    async def cleanup_old_memories(self, days: int = 30):
        """
        Borra automáticamente memorias más viejas que X días.
        
        Útil para evitar que la BD crezca infinitamente.
        
        Args:
            days: Días de antigüedad antes de borrar
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._cleanup_old_memories_sync, days)
    
    def _cleanup_old_memories_sync(self, days: int = 30):
        """Versión síncrona"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Borrar conversaciones viejas de baja importancia
            cursor.execute("""
                DELETE FROM conversations
                WHERE timestamp < ? AND importance = 'low'
            """, (cutoff_date,))
            
            # Borrar memorias viejas de baja importancia
            cursor.execute("""
                DELETE FROM memories
                WHERE created_at < ? AND importance = 'low'
            """, (cutoff_date,))
            
            conn.commit()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de la BD"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_stats_sync)
    
    def _get_stats_sync(self) -> Dict[str, Any]:
        """Versión síncrona"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Contar items en cada tabla
            cursor.execute("SELECT COUNT(*) FROM conversations")
            conversations_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM memories")
            memories_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_profile")
            preferences_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM entities")
            entities_count = cursor.fetchone()[0]
            
            # Tamaño del archivo
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                "name": "long_term",
                "conversations": conversations_count,
                "memories": memories_count,
                "preferences": preferences_count,
                "entities": entities_count,
                "total_items": conversations_count + memories_count + preferences_count + entities_count,
                "db_size_bytes": db_size,
                "db_path": str(self.db_path)
            }


class MemoryManager:
    """
    Orquestador de memoria.
    
    Coordina SHORT TERM + LONG TERM.
    Decide cuándo guardar dónde y cómo buscar.
    """
    
    def __init__(self, db_path: str = "data/jarvis_memory.db"):
        """
        Inicializa el manager de memoria.
        
        Args:
            db_path: Ruta de la BD para long term
        """
        self.short_term = ShortTermMemory(max_items=100)
        self.long_term = LongTermMemory(db_path)
        self.logger = self._get_logger()
    
    def _get_logger(self):
        """Obtiene el logger de Jarvis"""
        try:
            from .logger import JarvisLogger
            return JarvisLogger.get_logger("memory")
        except:
            import logging
            return logging.getLogger("memory")
    
    async def save(
        self,
        key: str,
        value: Any,
        importance: str = "normal",
        metadata: Dict = None,
        save_type: str = "both"
    ):
        """
        Guarda algo en memoria.
        
        Args:
            key: Clave única
            value: Valor
            importance: "low", "normal", "high"
            metadata: Info adicional
            save_type: "short_term", "long_term" o "both"
        
        Ejemplo:
            await memory_manager.save(
                key="user_name",
                value="González",
                importance="high",
                metadata={"type": "personal_info"}
            )
        """
        self.logger.info(f"Guardando en memoria", key=key, importance=importance)
        
        # Siempre guardar en short term
        if save_type in ["short_term", "both"]:
            self.short_term.save(key, value, metadata)
        
        # Guardar en long term si es importante
        if save_type in ["long_term", "both"] and importance in ["normal", "high"]:
            await self.long_term.save(key, value, metadata, importance)
    
    async def recall(self, key: str) -> Optional[MemoryItem]:
        """
        Busca un item por CLAVE EXACTA.
        
        Usar cuando sabes exactamente qué clave buscas.
        Buscar primero en short term (rápido), luego long term.
        
        Args:
            key: Clave exacta a buscar
        
        Returns:
            El item encontrado o None
        
        Ejemplo:
            item = await memory_manager.recall("user_name")
            if item:
                print(item.value)  # "González"
        """
        self.logger.info(f"Recall por clave exacta", key=key)
        
        # Buscar en short term primero (es más rápido y reciente)
        item = self.short_term.recall(key)
        if item:
            self.logger.debug(f"Encontrado en short term")
            return item
        
        # Si no está, buscar en long term
        item = await self.long_term.recall(key)
        if item:
            self.logger.debug(f"Encontrado en long term")
            # Guardar en short term para próxima búsqueda rápida
            self.short_term.save(key, item["value"], item["metadata"])
            return MemoryItem(
                key=item["key"],
                value=item["value"],
                importance=item["importance"],
                timestamp=datetime.fromisoformat(item["created_at"]),
                metadata=item["metadata"],
                source="long_term"
            )
        
        self.logger.debug(f"No encontrado en ninguna memoria")
        return None
    
    async def search(self, query: str, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Busca en memoria con LENGUAJE NATURAL (búsqueda libre).
        
        Usar cuando el usuario pregunta algo y no sabes la clave exacta.
        Busca tanto en conversaciones pasadas como en memorias generales.
        
        Args:
            query: Texto de búsqueda en lenguaje natural
            limit: Máximo de resultados por categoría
        
        Returns:
            {
                "conversaciones": [...],
                "memorias": [...]
            }
        
        Ejemplo:
            resultados = await memory_manager.search("¿qué música me gusta?")
            for conv in resultados["conversaciones"]:
                print(conv["user_message"])
        """
        self.logger.info(f"Búsqueda libre en memoria", query=query)
        
        conversaciones = await self.long_term.search_conversations(query, limit)
        memorias = await self.long_term.search_memories(query, limit)
        
        self.logger.debug(
            f"Búsqueda completada",
            conversaciones_encontradas=len(conversaciones),
            memorias_encontradas=len(memorias)
        )
        
        return {
            "conversaciones": conversaciones,
            "memorias": memorias
        }
    
    async def get_context(self) -> Dict[str, Any]:
        """Retorna el contexto actual del usuario"""
        return self.short_term.get_context()
    
    async def set_context(self, context_key: str, context_value: Any):
        """Establece el contexto actual"""
        self.short_term.set_context(context_key, context_value)
    
    async def save_conversation(self, user_message: str, agent_response: str, intent: str = None):
        """Guarda una conversación"""
        # Guardar en long term
        await self.long_term.save_conversation(user_message, agent_response, intent, importance="normal")
        
        # Guardar en short term también
        self.short_term.save(
            key=f"conversation_{datetime.now().timestamp()}",
            value={"user": user_message, "agent": agent_response},
            metadata={"intent": intent}
        )
    
    async def get_user_profile(self) -> Dict[str, str]:
        """Retorna el perfil del usuario"""
        return await self.long_term.get_user_profile()
    
    async def save_preference(self, key: str, value: str):
        """Guarda una preferencia del usuario"""
        await self.long_term.save_preference(key, value)
    
    async def save_entity(self, entity_type: str, entity_value: str):
        """Guarda una entidad extraída"""
        await self.long_term.save_entity(entity_type, entity_value)
    
    async def search_conversations(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca conversaciones previas (alias de search para compatibilidad)"""
        results = await self.search(query, limit)
        return results["conversaciones"]
    
    async def cleanup_old_memories(self, days: int = 30):
        """Limpia memorias antiguas"""
        self.logger.info(f"Limpiando memorias más viejas de {days} días")
        await self.long_term.cleanup_old_memories(days)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas completas"""
        return {
            "short_term": self.short_term.get_stats(),
            "long_term": await self.long_term.get_stats()
        }
    
    async def clear(self):
        """Limpia TODA la memoria (¡CUIDADO!)"""
        self.logger.warning("⚠️ Limpiando TODA la memoria")
        self.short_term.clear()
        # Para long term sería más complejo, por ahora solo short term
