from ..history.service import _get_connection
from .models import FeedbackRequest, FeedbackStats

def init_feedback_table():
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                guitar_id TEXT NOT NULL,
                rating TEXT NOT NULL CHECK(rating IN ('up','down')),
                query TEXT,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            );
        """)
        conn.commit()

# Вызов инициализации при импорте модуля
init_feedback_table()

def save_feedback(req: FeedbackRequest) -> int:
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO feedback (session_id, guitar_id, rating, query) VALUES (?, ?, ?, ?)",
            (req.session_id, req.guitar_id, req.rating, req.query)
        )
        conn.commit()
        return cursor.lastrowid

def get_feedback_stats() -> FeedbackStats:
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # Агрегируем общую статистику
        cursor.execute("SELECT COUNT(*), SUM(rating='up'), SUM(rating='down') FROM feedback")
        total, up, down = cursor.fetchone()

        total = total or 0
        up = up or 0
        down = down or 0
        ratio = (up / total) if total > 0 else 0.0

        # Агрегируем статистику по гитарам
        cursor.execute("SELECT guitar_id, SUM(rating='up'), SUM(rating='down') FROM feedback GROUP BY guitar_id")
        rows = cursor.fetchall()
        
        by_guitar = {row[0]: {"up": row[1] or 0, "down": row[2] or 0} for row in rows}

        return FeedbackStats(total=total, up=up, down=down, ratio=ratio, by_guitar=by_guitar)