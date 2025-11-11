import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from .logger import CustomLogger


class FeedbackDatabase:
    """
    Manages SQLite database for storing user feedback on chatbot responses.
    Supports feedback storage, retrieval, and batch operations for training.
    Also manages chat sessions and conversation history.
    """

    def __init__(self, db_path: str, logger: CustomLogger):
        self.db_path = db_path
        self.logger = logger
        self._initialize_database()

    def _initialize_database(self):
        """Create database and tables if they don't exist"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Create feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK(rating IN (0, 1)),
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Create chat_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create chat_messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    rl_used INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON feedback(timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rating 
                ON feedback(rating)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_updated 
                ON chat_sessions(updated_at DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON chat_messages(session_id, timestamp)
            """)

            conn.commit()
            conn.close()

            self.logger.info(f"Database initialized successfully at {self.db_path}")

        except sqlite3.Error as e:
            self.logger.error(f"Error initializing database: {e}")
            raise

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Error connecting to database: {e}")
            raise

    def save_feedback(
        self,
        question: str,
        answer: str,
        rating: int,
        session_id: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> int:
        """
        Save user feedback to database.

        Args:
            question: The user's question
            answer: The bot's response
            rating: 0 for negative, 1 for positive
            session_id: Optional session identifier
            metadata: Optional JSON string with additional data

        Returns:
            The ID of the inserted feedback record
        """
        if rating not in (0, 1):
            raise ValueError("Rating must be 0 (negative) or 1 (positive)")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO feedback (question, answer, rating, session_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (question, answer, rating, session_id, metadata),
            )

            feedback_id = cursor.lastrowid
            conn.commit()
            conn.close()

            self.logger.info(f"Saved feedback (ID: {feedback_id}, Rating: {rating})")
            return feedback_id

        except sqlite3.Error as e:
            self.logger.error(f"Error saving feedback: {e}")
            raise

    def get_all_feedback(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve all feedback records.

        Args:
            limit: Optional limit on number of records

        Returns:
            List of feedback dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM feedback ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()

            feedback_list = [dict(row) for row in rows]
            self.logger.info(f"Retrieved {len(feedback_list)} feedback records")

            return feedback_list

        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving feedback: {e}")
            return []

    def get_feedback_for_training(self, min_samples: int = 0) -> Tuple[List[str], List[int]]:
        """
        Get feedback data formatted for model training.

        Args:
            min_samples: Minimum number of samples required

        Returns:
            Tuple of (texts, labels) where texts are "Q: {q}\\nA: {a}" format
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT question, answer, rating 
                FROM feedback 
                ORDER BY timestamp ASC
            """)

            rows = cursor.fetchall()
            conn.close()

            if len(rows) < min_samples:
                self.logger.warning(f"Insufficient feedback samples: {len(rows)} < {min_samples}")
                return [], []

            texts = [f"Q: {row['question']}\nA: {row['answer']}" for row in rows]
            labels = [row["rating"] for row in rows]

            self.logger.info(
                f"Retrieved {len(texts)} samples for training "
                f"(Positive: {sum(labels)}, Negative: {len(labels) - sum(labels)})"
            )

            return texts, labels

        except sqlite3.Error as e:
            self.logger.error(f"Error getting training data: {e}")
            return [], []

    def get_recent_feedback(self, days: int = 7) -> List[Dict]:
        """
        Get feedback from the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of feedback dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM feedback 
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            """,
                (days,),
            )

            rows = cursor.fetchall()
            conn.close()

            feedback_list = [dict(row) for row in rows]
            self.logger.info(
                f"Retrieved {len(feedback_list)} feedback records from last {days} days"
            )

            return feedback_list

        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving recent feedback: {e}")
            return []

    def get_feedback_stats(self) -> Dict:
        """
        Get statistics about stored feedback.

        Returns:
            Dictionary with feedback statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) as total FROM feedback")
            total = cursor.fetchone()["total"]

            # Rating distribution
            cursor.execute("""
                SELECT rating, COUNT(*) as count 
                FROM feedback 
                GROUP BY rating
            """)
            rating_dist = {row["rating"]: row["count"] for row in cursor.fetchall()}

            # Recent feedback (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) as recent 
                FROM feedback 
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            recent_24h = cursor.fetchone()["recent"]

            conn.close()

            stats = {
                "total_feedback": total,
                "positive_count": rating_dist.get(1, 0),
                "negative_count": rating_dist.get(0, 0),
                "recent_24h": recent_24h,
            }

            self.logger.info(f"Feedback stats: {stats}")
            return stats

        except sqlite3.Error as e:
            self.logger.error(f"Error getting feedback stats: {e}")
            return {
                "total_feedback": 0,
                "positive_count": 0,
                "negative_count": 0,
                "recent_24h": 0,
            }

    def clear_old_feedback(self, days: int = 90) -> int:
        """
        Delete feedback older than N days.

        Args:
            days: Keep feedback from last N days, delete older

        Returns:
            Number of records deleted
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM feedback 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """,
                (days,),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()

            self.logger.info(f"Deleted {deleted_count} feedback records older than {days} days")
            return deleted_count

        except sqlite3.Error as e:
            self.logger.error(f"Error clearing old feedback: {e}")
            return 0

    # Chat Session Management Methods

    def create_session(self, session_id: str, title: str) -> bool:
        """
        Create a new chat session.

        Args:
            session_id: Unique session identifier
            title: Session title (max 50 chars recommended)

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO chat_sessions (id, title)
                VALUES (?, ?)
            """,
                (session_id, title[:50]),
            )  # Truncate to 50 chars

            conn.commit()
            conn.close()

            self.logger.info(f"Created session: {session_id} - '{title}'")
            return True

        except sqlite3.IntegrityError:
            self.logger.warning(f"Session {session_id} already exists")
            return False
        except sqlite3.Error as e:
            self.logger.error(f"Error creating session: {e}")
            return False

    def update_session_title(self, session_id: str, title: str) -> bool:
        """
        Update session title and timestamp.

        Args:
            session_id: Session identifier
            title: New title (max 50 chars recommended)

        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE chat_sessions 
                SET title = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (title[:50], session_id),
            )

            conn.commit()
            conn.close()

            self.logger.info(f"Updated session {session_id} title to '{title}'")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"Error updating session title: {e}")
            return False

    def update_session_timestamp(self, session_id: str) -> bool:
        """Update session's updated_at timestamp."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE chat_sessions 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (session_id,),
            )

            conn.commit()
            conn.close()
            return True

        except sqlite3.Error as e:
            self.logger.error(f"Error updating session timestamp: {e}")
            return False

    def get_all_sessions(self) -> List[Dict]:
        """
        Get all chat sessions ordered by most recent.

        Returns:
            List of session dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, title, created_at, updated_at
                FROM chat_sessions
                ORDER BY updated_at DESC
            """)

            rows = cursor.fetchall()
            conn.close()

            sessions = [dict(row) for row in rows]
            self.logger.info(f"Retrieved {len(sessions)} sessions")

            return sessions

        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving sessions: {e}")
            return []

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a single session by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM chat_sessions
                WHERE id = ?
            """,
                (session_id,),
            )

            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None

        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving session: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Delete messages first (foreign key constraint)
            cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            # Delete session
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))

            conn.commit()
            conn.close()

            self.logger.info(f"Deleted session: {session_id}")
            return True

        except sqlite3.Error as e:
            self.logger.error(f"Error deleting session: {e}")
            return False

    def save_message(self, session_id: str, role: str, content: str, rl_used: bool = False) -> int:
        """
        Save a chat message to a session.

        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            rl_used: Whether RL was used for this response

        Returns:
            Message ID if successful, -1 otherwise
        """
        if role not in ("user", "assistant"):
            raise ValueError("Role must be 'user' or 'assistant'")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, rl_used)
                VALUES (?, ?, ?, ?)
            """,
                (session_id, role, content, 1 if rl_used else 0),
            )

            message_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Update session timestamp
            self.update_session_timestamp(session_id)

            self.logger.info(f"Saved {role} message to session {session_id}")
            return message_id

        except sqlite3.Error as e:
            self.logger.error(f"Error saving message: {e}")
            return -1

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """
        Get all messages for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, session_id, role, content, timestamp, rl_used
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """,
                (session_id,),
            )

            rows = cursor.fetchall()
            conn.close()

            messages = [dict(row) for row in rows]
            self.logger.info(f"Retrieved {len(messages)} messages for session {session_id}")

            return messages

        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving messages: {e}")
            return []
