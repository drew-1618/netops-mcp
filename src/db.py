import sqlite3
from pathlib import Path
from typing import Any, Dict

DB_PATH = Path(__file__).resolve().parent.parent / "incidents.db"

def init_db() -> None:
    """
    Ensures the incidents table exists
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                ticket_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                severity TEXT NOT NULL,
                target TEXT NOT NULL,
                failing_layer TEXT NOT NULL,
                summary TEXT NOT NULL
                )
        """)

def log_incident(ticket: Dict[str, Any]) -> None:
    """
    Persists a generated incident ticket to a local SQLite database
    """

    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO incidents (
                ticket_id,
                created_at,
                status,
                severity,
                target,
                failing_layer,
                summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket["ticket_id"],
                ticket["created_at_utc"],
                ticket["status"],
                ticket["severity"],
                ticket["target"],
                ticket["failing_layer"],
                ticket["summary"],
        ),
        )
