"""Gestion des feedbacks avec SQLite"""

import sqlite3
import json
from datetime import datetime
from config import FEEDBACK_DB


class FeedbackManager:
    def __init__(self):
        self.db_path = FEEDBACK_DB
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    response TEXT,
                    feedback TEXT,
                    feedback_detail TEXT,
                    documents_used TEXT,
                    timestamp TEXT,
                    session_id TEXT
                )
            """)
    
    def add_feedback(self, question, response, feedback, feedback_detail, documents_used, session_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO feedbacks VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
                (question, response, feedback, feedback_detail, json.dumps(documents_used),
                 datetime.now().isoformat(), session_id)
            )
            return cursor.lastrowid
    
    def get_conversation_history(self, session_id, limit=10):
        """Récupère l'historique complet de la conversation"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM feedbacks WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            )
            return cursor.fetchall()