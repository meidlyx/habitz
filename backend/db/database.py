import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "habitz.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к полям через conn['name']
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Создание таблиц (перенесено из database.js)
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        avatar_url TEXT,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        streak INTEGER DEFAULT 0,
        best_streak INTEGER DEFAULT 0,
        freeze_count INTEGER DEFAULT 0,
        daily_xp INTEGER DEFAULT 0,
        boost_expires_at TEXT,
        theme TEXT DEFAULT 'dark',
        last_active_date TEXT,
        created_at TEXT DEFAULT (date('now'))
    );

    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        difficulty TEXT DEFAULT 'easy',
        xp_reward INTEGER DEFAULT 10,
        frequency TEXT DEFAULT 'daily',
        days_of_week TEXT,
        created_at TEXT DEFAULT (date('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS habit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        completed_date TEXT NOT NULL,
        xp_earned INTEGER DEFAULT 0,
        FOREIGN KEY (habit_id) REFERENCES habits(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        difficulty TEXT DEFAULT 'easy',
        xp_reward INTEGER DEFAULT 10,
        deadline TEXT,
        is_completed INTEGER DEFAULT 0,
        completed_at TEXT,
        created_at TEXT DEFAULT (date('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement_key TEXT NOT NULL,
        unlocked_at TEXT DEFAULT (date('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN boost_count INTEGER DEFAULT 0;")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Колонка уже существует

    conn.close()
