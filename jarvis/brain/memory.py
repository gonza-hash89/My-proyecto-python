"""
memory.py - Sistema de Memoria de Jarvis

SHORT TERM: RAM (conversación actual)
LONG TERM: SQLite (persistente)

recall(key) → búsqueda exacta
search(query) → búsqueda libre en lenguaje natural
"""

import sqlite3, json, asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
from collections import deque


@dataclass
class MemoryItem:
    key: str
    value: Any
    importance: str = "normal"
    timestamp: datetime = None
    metadata: Dict = None
    source: str = "short_term"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class ShortTermMemory:
    """RAM - conversación actual (máx 100 items)"""
    
    def __init__(self, max_items: int = 100):
        self.items = deque(maxlen=max_items)
        self.context = {}
    
    def save(self, key: str, value: Any, metadata: Dict = None):
        self.items.append(MemoryItem(key, value, metadata=metadata))
    
    def recall(self, key: str) -> Optional[MemoryItem]:
        return next((i for i in self.items if i.key == key), None)
    
    def recall_last(self, n: int = 5) -> List[MemoryItem]:
        return list(self.items)[-n:]
    
    def set_context(self, key: str, value: Any):
        self.context[key] = value
    
    def get_context(self, key: str = None):
        return self.context.get(key) if key else self.context
    
    def clear(self):
        self.items.clear()
        self.context.clear()
    
    def stats(self) -> Dict:
        return {
            "name": "short_term",
            "items": len(self.items),
            "context_keys": list(self.context.keys()),
        }


class LongTermMemory:
    """SQLite - persistente"""
    
    def __init__(self, db_path: str = "data/jarvis_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY, key TEXT UNIQUE, value TEXT,
                metadata TEXT, importance TEXT DEFAULT 'normal',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            c.execute("""CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT, agent_response TEXT, intent TEXT,
                importance TEXT DEFAULT 'normal')""")
            c.execute("""CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY, key TEXT UNIQUE, value TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
            conn.commit()
    
    async def save(self, key: str, value: Any, metadata: Dict = None, importance: str = "normal"):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_sync, key, value, metadata, importance)
    
    def _save_sync(self, key: str, value: Any, metadata: Dict, importance: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""INSERT OR REPLACE INTO memories (key, value, metadata, importance, accessed_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (key, json.dumps(value, default=str), json.dumps(metadata or {}), importance))
            conn.commit()
    
    async def recall(self, key: str) -> Optional[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._recall_sync, key)
    
    def _recall_sync(self, key: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT key, value, metadata, importance, created_at FROM memories WHERE key = ?", (key,))
            row = c.fetchone()
            if not row:
                return None
            c.execute("UPDATE memories SET accessed_at = CURRENT_TIMESTAMP WHERE key = ?", (key,))
            conn.commit()
            return {
                "key": row[0], "value": json.loads(row[1]),
                "metadata": json.loads(row[2]), "importance": row[3], "created_at": row[4]
            }
    
    async def search_conversations(self, query: str, limit: int = 5) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_conversations_sync, query, limit)
    
    def _search_conversations_sync(self, query: str, limit: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""SELECT timestamp, user_message, agent_response, intent FROM conversations
                WHERE user_message LIKE ? OR agent_response LIKE ?
                ORDER BY timestamp DESC LIMIT ?""",
                (f"%{query}%", f"%{query}%", limit))
            return [{"timestamp": r[0], "user_message": r[1], "agent_response": r[2], "intent": r[3]} 
                    for r in c.fetchall()]
    
    async def search_memories(self, query: str, limit: int = 5) -> List[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._search_memories_sync, query, limit)
    
    def _search_memories_sync(self, query: str, limit: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""SELECT key, value, metadata, importance, created_at FROM memories
                WHERE key LIKE ? OR value LIKE ? ORDER BY created_at DESC LIMIT ?""",
                (f"%{query}%", f"%{query}%", limit))
            return [{"key": r[0], "value": json.loads(r[1]), "metadata": json.loads(r[2]),
                     "importance": r[3], "created_at": r[4]} for r in c.fetchall()]
    
    async def save_conversation(self, user_msg: str, agent_resp: str, intent: str = None):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_conversation_sync, user_msg, agent_resp, intent)
    
    def _save_conversation_sync(self, user_msg: str, agent_resp: str, intent: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO conversations (user_message, agent_response, intent) VALUES (?, ?, ?)",
                (user_msg, agent_resp, intent))
            conn.commit()
    
    async def save_preference(self, key: str, value: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_preference_sync, key, value)
    
    def _save_preference_sync(self, key: str, value: str):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO user_profile (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
    
    async def get_user_profile(self) -> Dict[str, str]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_user_profile_sync)
    
    def _get_user_profile_sync(self) -> Dict[str, str]:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT key, value FROM user_profile")
            return {row[0]: row[1] for row in c.fetchall()}
    
    async def cleanup(self, days: int = 30):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._cleanup_sync, days)
    
    def _cleanup_sync(self, days: int):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            c.execute("DELETE FROM conversations WHERE timestamp < ? AND importance = 'low'", (cutoff,))
            c.execute("DELETE FROM memories WHERE created_at < ? AND importance = 'low'", (cutoff,))
            conn.commit()
    
    async def stats(self) -> Dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._stats_sync)
    
    def _stats_sync(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM conversations")
            conv = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM memories")
            mem = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM user_profile")
            pref = c.fetchone()[0]
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            return {"conversations": conv, "memories": mem, "preferences": pref, "db_size": db_size}


class MemoryManager:
    """Orquestador de memoria"""
    
    def __init__(self, db_path: str = "data/jarvis_memory.db"):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(db_path)
    
    async def save(self, key: str, value: Any, importance: str = "normal", metadata: Dict = None):
        """Guarda en short_term y long_term (si es importante)"""
        self.short_term.save(key, value, metadata)
        if importance in ["normal", "high"]:
            await self.long_term.save(key, value, metadata, importance)
    
    async def recall(self, key: str) -> Optional[MemoryItem]:
        """Búsqueda exacta por clave"""
        item = self.short_term.recall(key)
        if item:
            return item
        item = await self.long_term.recall(key)
        if item:
            self.short_term.save(key, item["value"], item["metadata"])
            return MemoryItem(
                key=item["key"], value=item["value"],
                importance=item["importance"],
                timestamp=datetime.fromisoformat(item["created_at"]),
                metadata=item["metadata"], source="long_term"
            )
        return None
    
    async def search(self, query: str, limit: int = 5) -> Dict[str, List[Dict]]:
        """Búsqueda libre en lenguaje natural"""
        convs = await self.long_term.search_conversations(query, limit)
        mems = await self.long_term.search_memories(query, limit)
        return {"conversaciones": convs, "memorias": mems}
    
    async def save_conversation(self, user_msg: str, agent_resp: str, intent: str = None):
        """Guarda conversación en ambas memorias"""
        await self.long_term.save_conversation(user_msg, agent_resp, intent)
        self.short_term.save(f"conv_{datetime.now().timestamp()}",
                           {"user": user_msg, "agent": agent_resp},
                           metadata={"intent": intent})
    
    async def save_preference(self, key: str, value: str):
        await self.long_term.save_preference(key, value)
    
    async def get_user_profile(self) -> Dict[str, str]:
        return await self.long_term.get_user_profile()
    
    async def cleanup(self, days: int = 30):
        await self.long_term.cleanup(days)
    
    async def stats(self) -> Dict:
        return {
            "short_term": self.short_term.stats(),
            "long_term": await self.long_term.stats()
        }
    
    async def get_context(self) -> Dict:
        return self.short_term.get_context()
    
    async def set_context(self, key: str, value: Any):
        self.short_term.set_context(key, value)
    
    async def clear(self):
        self.short_term.clear()
