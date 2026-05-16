from ..history.service import _get_connection
from .models import FeedbackRequest, FeedbackStats
from . import feedback_store

def init_feedback_table():
    with _get_connection() as conn:
        feedback_store.init_feedback_table(conn)
        conn.commit()

# Вызов инициализации при импорте модуля
init_feedback_table()

def save_feedback(req: FeedbackRequest) -> int:
    with _get_connection() as conn:
        cursor = feedback_store.insert_feedback(conn, req)
        conn.commit()
        return cursor.lastrowid

def get_feedback_stats(user_id: int) -> FeedbackStats:
    with _get_connection() as conn:
        total, up, down = feedback_store.select_feedback_totals(conn, user_id)
        ratio = (up / total) if total > 0 else 0.0
        by_guitar = feedback_store.select_feedback_by_guitar(conn, user_id)
        return FeedbackStats(total=total, up=up, down=down, ratio=ratio, by_guitar=by_guitar)
