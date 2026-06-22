import json
from datetime import datetime, timedelta

from db.database import get_db_connection
from flask import Blueprint, g, jsonify, request
from middleware.auth import token_required

habits_bp = Blueprint("habits", __name__)


@habits_bp.route("/", methods=["GET"])
@token_required
def get_habits():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем все привычки с флагом выполнения на сегодня
    rows = cursor.execute(
        """
        SELECT h.*, 
        CASE WHEN hl.id IS NOT NULL THEN 1 ELSE 0 END as completed_today
        FROM habits h
        LEFT JOIN habit_logs hl 
        ON h.id = hl.habit_id 
        AND hl.user_id = ? 
        AND hl.completed_date = date('now')
        WHERE h.user_id = ?
    """,
        (g.user_id, g.user_id),
    ).fetchall()

    habits = [dict(row) for row in rows]

    # Соответствие дней недели: в JS 0=Вс, 1=Пн, ..., 6=Сб
    # В Python datetime.weekday() выдает 0=Пн, ..., 6=Вс
    now = datetime.now()
    today_js = (now.weekday() + 1) % 7

    filtered = []
    for h in habits:
        if h["frequency"] == "daily":
            filtered.append(h)
            continue
        if not h["days_of_week"]:
            filtered.append(h)
            continue
        try:
            days = json.loads(h["days_of_week"])
            if today_js in days:
                filtered.append(h)
        except Exception:
            filtered.append(h)

    conn.close()
    return jsonify(filtered)


@habits_bp.route("/", methods=["POST"])
@token_required
def create_habit():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    difficulty = data.get("difficulty", "easy")
    frequency = data.get("frequency", "daily")
    days_of_week = data.get("days_of_week")

    if not title:
        return jsonify({"error": "Название обязательно"}), 400

    xp_reward = 30 if difficulty == "hard" else (20 if difficulty == "medium" else 10)
    days_str = json.dumps(days_of_week) if days_of_week else None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO habits (user_id, title, description, difficulty, xp_reward, frequency, days_of_week)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (g.user_id, title, description, difficulty, xp_reward, frequency, days_str),
    )

    habit_id = cursor.lastrowid
    conn.commit()

    habit = cursor.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
    conn.close()
    return jsonify(dict(habit))


@habits_bp.route("/<int:habit_id>", methods=["DELETE"])
@token_required
def delete_habit(habit_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    habit = cursor.execute(
        "SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, g.user_id)
    ).fetchone()
    if not habit:
        conn.close()
        return jsonify({"error": "Привычка не найдена"}), 404

    cursor.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
    cursor.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@habits_bp.route("/<int:habit_id>/complete", methods=["POST"])
@token_required
def complete_habit(habit_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    habit = cursor.execute(
        "SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, g.user_id)
    ).fetchone()
    if not habit:
        conn.close()
        return jsonify({"error": "Привычка не найдена"}), 404

    already_done = cursor.execute(
        """
        SELECT id FROM habit_logs 
        WHERE habit_id = ? AND user_id = ? AND completed_date = date('now')
    """,
        (habit_id, g.user_id),
    ).fetchone()

    if already_done:
        conn.close()
        return jsonify({"error": "Привычка уже выполнена сегодня"}), 400

    user = cursor.execute("SELECT * FROM users WHERE id = ?", (g.user_id,)).fetchone()
    xp_to_add = habit["xp_reward"]

    cursor.execute(
        """
        INSERT INTO habit_logs (habit_id, user_id, completed_date, xp_earned)
        VALUES (?, ?, date('now'), ?)
    """,
        (habit_id, g.user_id, xp_to_add),
    )

    new_xp = user["xp"] + xp_to_add
    new_daily_xp = user["daily_xp"] + xp_to_add

    levels = [0, 200, 500, 1000, 2000, 3500, 5500, 8000, 11000, 15000]
    new_level = 1
    for i in range(len(levels) - 1, -1, -1):
        if new_xp >= levels[i]:
            new_level = i + 1
            break

    today_str = datetime.now().date().isoformat()
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
