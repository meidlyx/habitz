from datetime import datetime, timedelta

from db.database import get_db_connection
from flask import Blueprint, g, jsonify, request
from middleware.auth import token_required

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/", methods=["GET"])
@token_required
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT * FROM tasks WHERE user_id = ?
        ORDER BY is_completed ASC, created_at DESC
    """,
        (g.user_id,),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@tasks_bp.route("/", methods=["POST"])
@token_required
def create_task():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    difficulty = data.get("difficulty", "easy")
    deadline = data.get("deadline")

    if not title:
        return jsonify({"error": "Название обязательно"}), 400

    xp_reward = 30 if difficulty == "hard" else (20 if difficulty == "medium" else 10)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tasks (user_id, title, description, difficulty, xp_reward, deadline)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (g.user_id, title, description, difficulty, xp_reward, deadline or None),
    )

    task_id = cursor.lastrowid
    conn.commit()
    task = cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return jsonify(dict(task))


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@token_required
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    task = cursor.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, g.user_id)
    ).fetchone()
    if not task:
        conn.close()
        return jsonify({"error": "Задача не найдена"}), 404

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@tasks_bp.route("/<int:task_id>/complete", methods=["POST"])
@token_required
def complete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    task = cursor.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, g.user_id)
    ).fetchone()
    if not task:
        conn.close()
        return jsonify({"error": "Задача не найдена"}), 404

    if task["is_completed"]:
        conn.close()
        return jsonify({"error": "Задача уже выполнена"}), 400

    today_str = datetime.now().date().isoformat()
    if task["deadline"] and task["deadline"] < today_str:
        conn.close()
        return jsonify({"error": "Задача просрочена"}), 400

    user = cursor.execute("SELECT * FROM users WHERE id = ?", (g.user_id,)).fetchone()
    xp_to_add = task["xp_reward"]
    new_xp = user["xp"] + xp_to_add
    new_daily_xp = user["daily_xp"] + xp_to_add

    levels = [0, 200, 500, 1000, 2000, 3500, 5500, 8000, 11000, 15000]
    new_level = 1
    for i in range(len(levels) - 1, -1, -1):
        if new_xp >= levels[i]:
            new_level = i + 1
            break

    yesterday_str = (datetime.now() - timedelta(days=1)).date().isoformat()
    new_streak = user["streak"]

    if user["last_active_date"] == yesterday_str:
        new_streak = user["streak"] + 1
    elif user["last_active_date"] != today_str:
        new_streak = 1

    new_best_streak = max(user["best_streak"], new_streak)
    boost_expires_at = user["boost_expires_at"]

    if new_level > user["level"]:
        boost_days_list = [0, 0, 0, 3, 0, 5, 0, 0, 0, 7, 0]
        boost_days = (
            boost_days_list[new_level] if new_level < len(boost_days_list) else 0
        )
        if boost_days > 0:
            boost_expires_at = (
                (datetime.now() + timedelta(days=boost_days)).date().isoformat()
            )

    cursor.execute(
        "UPDATE tasks SET is_completed = 1, completed_at = ? WHERE id = ?",
        (today_str, task_id),
    )

    cursor.execute(
        """
        UPDATE users SET 
        xp = ?, daily_xp = ?, level = ?,
        streak = ?, best_streak = ?,
        last_active_date = ?, boost_expires_at = ?
        WHERE id = ?
    """,
        (
            new_xp,
            new_daily_xp,
            new_level,
            new_streak,
            new_best_streak,
            today_str,
            boost_expires_at,
            g.user_id,
        ),
    )

    if new_level > user["level"]:
        freeze_bonus_list = [0, 0, 2, 0, 3, 0, 3, 0, 4, 0, 5]
        freeze_bonus = (
            freeze_bonus_list[new_level] if new_level < len(freeze_bonus_list) else 0
        )
        if freeze_bonus > 0:
            cursor.execute(
                "UPDATE users SET freeze_count = freeze_count + ? WHERE id = ?",
                (freeze_bonus, g.user_id),
            )

    conn.commit()
    conn.close()

    return jsonify(
        {
            "success": True,
            "xp_earned": xp_to_add,
            "total_xp": new_xp,
            "level": new_level,
            "streak": new_streak,
            "leveled_up": new_level > user["level"],
        }
    )
