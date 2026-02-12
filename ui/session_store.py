"""
Session Storage using SQLite
Stores UI sessions, messages, and extracted intelligence
Completely independent from main app's session management
"""

import sqlite3
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionStore:
    """SQLite-based session storage"""
    
    def __init__(self, db_path: str = "ui/sessions.db"):
        """Initialize database"""
        self.db_path = db_path
        
        # Ensure ui directory exists
        Path("ui").mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        logger.info(f"SessionStore initialized with database: {db_path}")
    
    def _init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                scam_detected INTEGER DEFAULT 0,
                scam_type TEXT,
                confidence REAL,
                intelligence TEXT DEFAULT '{}'
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id: str) -> Dict:
        """Create a new session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        try:
            cursor.execute("""
                INSERT INTO sessions (session_id, created_at, updated_at, intelligence)
                VALUES (?, ?, ?, ?)
            """, (session_id, now, now, "{}"))
            conn.commit()
            
            logger.info(f"Created session: {session_id}")
            
            return {
                "session_id": session_id,
                "created_at": now,
                "updated_at": now,
                "scam_detected": False,
                "scam_type": None,
                "confidence": None,
                "intelligence": {}
            }
        except sqlite3.IntegrityError:
            logger.warning(f"Session already exists: {session_id}")
            return self.get_session(session_id)
        finally:
            conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, created_at, updated_at, scam_detected, 
                   scam_type, confidence, intelligence
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "session_id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "scam_detected": bool(row[3]),
            "scam_type": row[4],
            "confidence": row[5],
            "intelligence": json.loads(row[6]) if row[6] else {}
        }
    
    def add_message(self, session_id: str, sender: str, text: str, timestamp: int):
        """Add a message to the session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        try:
            cursor.execute("""
                INSERT INTO messages (session_id, sender, text, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, sender, text, timestamp, now))
            
            # Update session timestamp
            cursor.execute("""
                UPDATE sessions
                SET updated_at = ?
                WHERE session_id = ?
            """, (now, session_id))
            
            conn.commit()
            logger.debug(f"Added message to session {session_id}: {sender}")
        finally:
            conn.close()
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history in format expected by honeypot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT sender, text, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "sender": row[0],
                "text": row[1],
                "timestamp": row[2]
            }
            for row in rows
        ]
    
    def get_message_count(self, session_id: str) -> int:
        """Get total message count for session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM messages WHERE session_id = ?
        """, (session_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def update_intelligence(self, session_id: str, intelligence: Dict):
        """Update intelligence data for session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        intelligence_json = json.dumps(intelligence)
        
        try:
            cursor.execute("""
                UPDATE sessions
                SET intelligence = ?, updated_at = ?
                WHERE session_id = ?
            """, (intelligence_json, now, session_id))
            
            conn.commit()
            logger.debug(f"Updated intelligence for session {session_id}")
        finally:
            conn.close()
    
    def update_scam_status(self, session_id: str, scam_detected: bool, 
                          scam_type: str = None, confidence: float = None):
        """Update scam detection status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        try:
            cursor.execute("""
                UPDATE sessions
                SET scam_detected = ?, scam_type = ?, confidence = ?, updated_at = ?
                WHERE session_id = ?
            """, (int(scam_detected), scam_type, confidence, now, session_id))
            
            conn.commit()
            logger.info(f"Updated scam status for session {session_id}: {scam_type}")
        finally:
            conn.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete messages first (foreign key)
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            
            # Delete session
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logger.info(f"Deleted session: {session_id}")
            
            return deleted
        finally:
            conn.close()
    
    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """List recent sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, created_at, updated_at, scam_detected, scam_type
            FROM sessions
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "session_id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "scam_detected": bool(row[3]),
                "scam_type": row[4]
            }
            for row in rows
        ]
    
    def cleanup_old_sessions(self, days: int = 7):
        """Delete sessions older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff = cutoff.isoformat()
        
        try:
            cursor.execute("""
                DELETE FROM sessions
                WHERE created_at < datetime(?, '-' || ? || ' days')
            """, (cutoff, days))
            
            deleted = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted} old sessions")
            return deleted
        finally:
            conn.close()
