"""
LLM Response Caching Module
============================

Implements persistent caching for LLM responses to reduce costs and improve speed.
Uses SQLite for reliable storage.
"""

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime
from threading import Lock
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Persistent cache for LLM responses using SQLite.
    
    Cache key is generated from:
    - Model name
    - Temperature
    - System prompt
    - User prompt
    - Schema/output format
    """
    
    def __init__(self, cache_dir: str = ".cache", enabled: bool = True):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache database
            enabled: Whether caching is enabled
        """
        self.cache_dir = cache_dir
        self.enabled = enabled
        self._lock = Lock()
        
        if self.enabled:
            self._ensure_cache_dir()
            self._init_db()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_db_path(self) -> str:
        """Get path to cache database."""
        return os.path.join(self.cache_dir, "llm_cache.db")
    
    def _init_db(self):
        """Initialize the cache database."""
        db_path = self._get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model 
                ON cache(model)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON cache(created_at)
            """)
            
            conn.commit()
        
        logger.info(f"Cache database initialized at {db_path}")
    
    def _generate_cache_key(
        self,
        model: str,
        temperature: float,
        system_prompt: str,
        user_prompt: str,
        schema_name: Optional[str] = None
    ) -> str:
        """
        Generate a cache key from request parameters.
        
        Args:
            model: Model name
            temperature: Temperature setting
            system_prompt: System prompt
            user_prompt: User prompt
            schema_name: Optional schema name for structured outputs
            
        Returns:
            Cache key string
        """
        # Create a deterministic string representation
        key_parts = [
            f"model={model}",
            f"temp={temperature:.2f}",
            f"system={system_prompt}",
            f"user={user_prompt}",
        ]
        
        if schema_name:
            key_parts.append(f"schema={schema_name}")
        
        key_string = "|".join(key_parts)
        
        # Generate hash
        cache_key = hashlib.sha256(key_string.encode('utf-8')).hexdigest()
        
        return cache_key
    
    def get(
        self,
        model: str,
        temperature: float,
        system_prompt: str,
        user_prompt: str,
        schema_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a cached response if available.
        
        Args:
            model: Model name
            temperature: Temperature setting
            system_prompt: System prompt
            user_prompt: User prompt
            schema_name: Optional schema name
            
        Returns:
            Cached response dict or None if not found
        """
        if not self.enabled:
            return None
        
        cache_key = self._generate_cache_key(
            model, temperature, system_prompt, user_prompt, schema_name
        )
        
        with self._lock:
            try:
                db_path = self._get_db_path()
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT response_json, input_tokens, output_tokens
                        FROM cache
                        WHERE cache_key = ?
                    """, (cache_key,))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        # Update access stats
                        cursor.execute("""
                            UPDATE cache
                            SET last_accessed = ?,
                                access_count = access_count + 1
                            WHERE cache_key = ?
                        """, (datetime.now().isoformat(), cache_key))
                        
                        conn.commit()
                        
                        response = json.loads(row['response_json'])
                        
                        logger.info(f"Cache HIT for key {cache_key[:16]}...")
                        
                        return {
                            "response": response,
                            "input_tokens": row['input_tokens'],
                            "output_tokens": row['output_tokens'],
                            "cache_hit": True
                        }
                    else:
                        logger.debug(f"Cache MISS for key {cache_key[:16]}...")
                        return None
                        
            except Exception as e:
                logger.error(f"Error reading from cache: {e}")
                return None
    
    def put(
        self,
        model: str,
        temperature: float,
        system_prompt: str,
        user_prompt: str,
        response: Any,
        input_tokens: int,
        output_tokens: int,
        schema_name: Optional[str] = None
    ):
        """
        Store a response in the cache.
        
        Args:
            model: Model name
            temperature: Temperature setting
            system_prompt: System prompt
            user_prompt: User prompt
            response: Response to cache
            input_tokens: Input token count
            output_tokens: Output token count
            schema_name: Optional schema name
        """
        if not self.enabled:
            return
        
        cache_key = self._generate_cache_key(
            model, temperature, system_prompt, user_prompt, schema_name
        )
        
        # Hash the prompts for storage (for statistics/debugging)
        prompt_hash = hashlib.sha256(
            (system_prompt + user_prompt).encode('utf-8')
        ).hexdigest()[:16]
        
        with self._lock:
            try:
                db_path = self._get_db_path()
                with sqlite3.connect(db_path) as conn:
                    now = datetime.now().isoformat()
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO cache
                        (cache_key, model, temperature, prompt_hash, response_json,
                         input_tokens, output_tokens, created_at, last_accessed)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cache_key,
                        model,
                        temperature,
                        prompt_hash,
                        json.dumps(response),
                        input_tokens,
                        output_tokens,
                        now,
                        now
                    ))
                    
                    conn.commit()
                
                logger.debug(f"Cached response for key {cache_key[:16]}...")
                
            except Exception as e:
                logger.error(f"Error writing to cache: {e}")
    
    def clear(self):
        """Clear all cached entries."""
        if not self.enabled:
            return
        
        with self._lock:
            try:
                db_path = self._get_db_path()
                with sqlite3.connect(db_path) as conn:
                    conn.execute("DELETE FROM cache")
                    conn.commit()
                
                logger.info("Cache cleared")
                
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled:
            return {
                "enabled": False,
                "total_entries": 0,
                "total_size_bytes": 0
            }
        
        with self._lock:
            try:
                db_path = self._get_db_path()
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Get entry count
                    cursor.execute("SELECT COUNT(*) as count FROM cache")
                    total_entries = cursor.fetchone()['count']
                    
                    # Get total access count
                    cursor.execute("SELECT SUM(access_count) as total FROM cache")
                    total_accesses = cursor.fetchone()['total'] or 0
                    
                    # Get database size
                    db_size = os.path.getsize(db_path)
                    
                    return {
                        "enabled": True,
                        "total_entries": total_entries,
                        "total_accesses": total_accesses,
                        "total_size_bytes": db_size,
                        "db_path": db_path
                    }
                    
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
                return {
                    "enabled": True,
                    "error": str(e)
                }
