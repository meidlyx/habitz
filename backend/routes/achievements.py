from db.database import get_db_connection
from flask import Blueprint, g, jsonify, request
from middleware.auth import token_required

achievements_bp = Blueprint("achievements", __name__)

ACHIEVEMENTS = [
    {
        "key": "first_step",
        "title": "Первый шаг",
        "description": "Выполни первую привычку",
        "category": "Привычки",
        "goal": 1,
        "xp_bonus": 20,
    },
    {
        "key": "week_streak",
        "title": "Неделя подряд",
        "description": "7 дней без пропуска",
        "category": "Серия",
        "goal": 7,
        "xp_bonus": 50,
    },
    {
        "key": "month_streak",
        "title": "Месяц силы",
        "description": "30 дней без пропуска",
        "category": "Серия",
        "goal": 30,
        "xp_bonus": 150,
    },
    {
        "key": "tasks_10",
        "title": "Трудяга",
        "description": "Выполни 10 задач",
        "category": "Задачи",
        "goal": 10,
        "xp_bonus": 30,
    },
    {
        "key": "habits_50",
        "title": "Машина привычек",
        "description": "Выполни 50 привычек суммарно",
        "category": "Привычки",
        "goal": 50,
        "xp_bonus": 100,
    },
    {
        "key": "early_bird",
        "title": "Ранняя пташка",
        "description": "Выполни привычку до 8:00",
        "category": "Активность",
        "goal": 1,
        "xp_bonus": 15,
    },
    {
        "key": "perfectionist",
        "title": "Перфекционист",
        "description": "0 просроченных задач за месяц",
        "category": "Задачи",
        "goal": 1,
        "xp_bonus": 80,
    },
    {
        "key": "xp_1000",
        "title": "Богатый опытом",
        "description": "Набери 1000 XP суммарно",
        "category": "Опыт",
        "goal": 1000,
        "xp_bonus": 50,
    },
    {
        "key": "habits_200",
        "title": "Легенда привычек",
        "description": "Выполни 200 привычек суммарно",
        "category": "Привычки",
        "goal": 200,
        "xp_bonus": 200,
    },
    {
        "key": "no_freeze_14",
        "title": "Без страховки",
        "description": "Серия 14 дней без заморозки",
        "category": "Серия",
        "goal": 14,
        "xp_bonus": 70,
    },
]


@achievements_bp.route("/", methods=["GET"])
@token_required
def get_achievements():
    conn = get_db_connection()
    cursor = conn.cursor()

    user = cursor.execute("SELECT * FROM users WHERE id = ?", (g.user_id,)).fetchone()
    unlocked_rows = cursor.execute(
        "SELECT achievement_key FROM user_achievements WHERE user_id = ?", (g.user_id,)
    ).fetchall()
    unlocked_keys = [r["achievement_key"] for r in unlocked_rows]

    habits_completed = cursor.execute(
        "SELECT COUNT(*) as count FROM habit_logs WHERE user_id = ?", (g.user_id,)
    ).fetchone()["count"]
    tasks_completed = cursor.execute(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND is_completed = 1",
        (g.user_id,),
    ).fetchone()["count"]

    conn.close()

    result = []
    for a in ACHIEVEMENTS:
        progress = 0
        key = a["key"]

        if key == "first_step":
            progress = min(habits_completed, 1)
        elif key == "week_streak":
            progress = min(user["streak"], 7)
        elif key == "month_streak":
            progress = min(user["streak"], 30)
        elif key == "tasks_10":
            progress = min(tasks_completed, 10)
        elif key == "habits_50":
            progress = min(habits_completed, 50)
        elif key == "habits_200":
            progress = min(habits_completed, 200)
        elif key == "xp_1000":
            progress = min(user["xp"], 1000)
        elif key == "no_freeze_14":
            progress = min(user["streak"], 14)
        elif key in unlocked_keys:
            progress = a["goal"]

        achievement_data = dict(a)
        achievement_data.update(
            {"progress": progress, "unlocked": key in unlocked_keys}
        )
        result.append(achievement_data)

    return jsonify(result)


@achievements_bp.route("/check", methods=["POST"])
@token_required
def check_achievements():
    conn = get_db_connection()
    cursor = conn.cursor()

    user = cursor.execute("SELECT * FROM users WHERE id = ?", (g.user_id,)).fetchone()
    unlocked_rows = cursor.execute(
        "SELECT achievement_key FROM user_achievements WHERE user_id = ?", (g.user_id,)
    ).fetchall()
    unlocked_keys = [r["achievement_key"] for r in unlocked_rows]

    habits_completed = cursor.execute(
        "SELECT COUNT(*) as count FROM habit_logs WHERE user_id = ?", (g.user_id,)
    ).fetchone()["count"]
    tasks_completed = cursor.execute(
        "SELECT COUNT(*) as count FROM tasks WHERE user_id = ? AND is_completed = 1",
        (g.user_id,),
    ).fetchone()["count"]

    newly_unlocked = []

    def check_and_insert(key, condition):
        if key not in unlocked_keys and condition:
            cursor.execute(
                "INSERT INTO user_achievements (user_id, achievement_key) VALUES (?, ?)",
                (g.user_id, key),
            )
            achievement = next((a for a in ACHIEVEMENTS if a["key"] == key), None)
            if achievement and achievement["xp_bonus"] > 0:
                cursor.execute(
                    "UPDATE users SET xp = xp + ? WHERE id = ?",
                    (achievement["xp_bonus"], g.user_id),
                )
            newly_unlocked.append(achievement)

    check_and_insert("first_step", habits_completed >= 1)
    check_and_insert("week_streak", user["streak"] >= 7)
    check_and_insert("month_streak", user["streak"] >= 30)
    check_and_insert("tasks_10", tasks_completed >= 10)
    check_and_insert("habits_50", habits_completed >= 50)
    check_and_insert("habits_200", habits_completed >= 200)
    check_and_insert("xp_1000", user["xp"] >= 1000)
    check_and_insert("no_freeze_14", user["streak"] >= 14)

    conn.commit()
    conn.close()
    return jsonify({"newly_unlocked": newly_unlocked})
