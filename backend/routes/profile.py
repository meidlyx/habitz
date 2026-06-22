import random
from datetime import datetime, timedelta

from db.database import get_db_connection
from flask import Blueprint, g, jsonify, request
from middleware.auth import token_required

profile_bp = Blueprint("profile", __name__)

LEVELS = [0, 200, 500, 1000, 2000, 3500, 5500, 8000, 11000, 15000]
LEVEL_NAMES = [
    "Новичок",
    "Участник",
    "Активный",
    "Упорный",
    "Целеустремлённый",
    "Опытный",
    "Эксперт",
    "Мастер",
    "Элита",
    "Легенда",
]


@profile_bp.route("/", methods=["GET"])
@token_required
def get_profile():
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute(
        """
        SELECT id, name, avatar_url, xp, level, streak, best_streak, 
        freeze_count, boost_count, daily_xp, boost_expires_at, theme, created_at
        FROM users WHERE id = ?
    """,
        (g.user_id,),
    ).fetchone()
    conn.close()

    user_dict = dict(user)
    lvl = user_dict["level"]

    next_level_xp = LEVELS[lvl] if lvl < len(LEVELS) else None
    current_level_xp = LEVELS[lvl - 1] if lvl - 1 < len(LEVELS) else 0
    level_name = LEVEL_NAMES[lvl - 1] if lvl - 1 < len(LEVEL_NAMES) else "Легенда"

    boost_active = False
    if user_dict["boost_expires_at"]:
        try:
            boost_active = (
                datetime.fromisoformat(user_dict["boost_expires_at"]) > datetime.now()
            )
        except ValueError:
            boost_active = (
                user_dict["boost_expires_at"] > datetime.now().date().isoformat()
            )

    user_dict.update(
        {
            "level_name": level_name,
            "next_level_xp": next_level_xp,
            "current_level_xp": current_level_xp,
            "boost_active": boost_active,
        }
    )
    return jsonify(user_dict)


@profile_bp.route("/stats", methods=["GET"])
@token_required
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    user = cursor.execute("SELECT * FROM users WHERE id = ?", (g.user_id,)).fetchone()
    habits_count = cursor.execute(
        "SELECT COUNT(*) as count FROM habit_logs WHERE user_id = ?", (g.user_id,)
    ).fetchone()["count"]
    tasks_count = cursor.execute(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND is_completed = 1",
        (g.user_id,),
    ).fetchone()["count"]
    achievements_count = cursor.execute(
        "SELECT COUNT(*) as count FROM user_achievements WHERE user_id = ?",
        (g.user_id,),
    ).fetchone()["count"]

    conn.close()

    boost_active = False
    if user["boost_expires_at"]:
        boost_active = user["boost_expires_at"] > datetime.now().date().isoformat()

    return jsonify(
        {
            "xp": user["xp"],
            "streak": user["streak"],
            "best_streak": user["best_streak"],
            "habits_completed": habits_count,
            "tasks_completed": tasks_count,
            "achievements": achievements_count,
            "freeze_count": user["freeze_count"],
            "boost_active": boost_active,
        }
    )


@profile_bp.route("/activity", methods=["GET"])
@token_required
def get_activity():
    conn = get_db_connection()
    cursor = conn.cursor()

    habit_activity = cursor.execute(
        """
        SELECT completed_date as date, COUNT(*) as count
        FROM habit_logs
        WHERE user_id = ? AND completed_date >= date('now', '-90 days')
        GROUP BY completed_date
    """,
        (g.user_id,),
    ).fetchall()

    task_activity = cursor.execute(
        """
        SELECT completed_at as date, COUNT(*) as count
        FROM tasks
        WHERE user_id = ? AND is_completed = 1 
        AND completed_at >= date('now', '-90 days')
        GROUP BY completed_at
    """,
        (g.user_id,),
    ).fetchall()

    conn.close()

    activity_map = {}
    for row in habit_activity:
        if row["date"]:
            activity_map[row["date"]] = activity_map.get(row["date"], 0) + row["count"]
    for row in task_activity:
        if row["date"]:
            activity_map[row["date"]] = activity_map.get(row["date"], 0) + row["count"]

    return jsonify(activity_map)


@profile_bp.route("/use-freeze", methods=["POST"])
@token_required
def use_freeze():
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT freeze_count FROM users WHERE id = ?", (g.user_id,)
    ).fetchone()

    if user["freeze_count"] <= 0:
        conn.close()
        return jsonify({"error": "Нет заморозок"}), 400

    new_freeze = user["freeze_count"] - 1
    cursor.execute(
        "UPDATE users SET freeze_count = ? WHERE id = ?", (new_freeze, g.user_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "freeze_count": new_freeze})


@profile_bp.route("/use-boost", methods=["POST"])
@token_required
def use_boost():
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute(
        "SELECT boost_count FROM users WHERE id = ?", (g.user_id,)
    ).fetchone()

    if not user["boost_count"] or user["boost_count"] <= 0:
        conn.close()
        return jsonify({"error": "Нет кото-бонусов"}), 400

    boost_days = random.randint(1, 7)
    boost_date = (datetime.now() + timedelta(days=boost_days)).date().isoformat()

    cursor.execute(
        "UPDATE users SET boost_count = boost_count - 1, boost_expires_at = ? WHERE id = ?",
        (boost_date, g.user_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "boost_expires_at": boost_date})


@profile_bp.route("/reset-stats", methods=["POST"])
@token_required
def reset_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users SET xp = 0, level = 1, streak = 0, best_streak = 0,
        daily_xp = 0, freeze_count = 0, boost_expires_at = null,
        last_active_date = null WHERE id = ?
    """,
        (g.user_id,),
    )

    cursor.execute("DELETE FROM habit_logs WHERE user_id = ?", (g.user_id,))
    cursor.execute(
        "UPDATE tasks SET is_completed = 0, completed_at = null WHERE user_id = ?",
        (g.user_id,),
    )
    cursor.execute("DELETE FROM user_achievements WHERE user_id = ?", (g.user_id,))

    conn.commit()
    conn.close()
    return jsonify({"success": True})
