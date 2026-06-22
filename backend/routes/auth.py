import os

import bcrypt
import jwt
from db.database import get_db_connection
from flask import Blueprint, jsonify, request

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Заполните все поля"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    existing_user = cursor.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    if existing_user:
        conn.close()
        return jsonify({"error": "Email уже занят"}), 400

    # Хеширование пароля
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(10)
    ).decode("utf-8")

    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, hashed_password),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    jwt_secret = (
        os.getenv("JWT_SECRET")
        or os.getenv("SECRET_KEY")
        or "fallback_secret_key_98765"
    )
    token = jwt.encode({"userId": user_id}, jwt_secret, algorithm="HS256")
    return jsonify({"token": token, "name": name})


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Заполните все поля"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    user = cursor.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "Неверный email или пароль"}), 400

    # Проверка хэша
    if not bcrypt.checkpw(
        password.encode("utf-8"), user["password_hash"].encode("utf-8")
    ):
        conn.close()
        return jsonify({"error": "Неверный email или пароль"}), 400

    conn.close()

    jwt_secret = (
        os.getenv("JWT_SECRET")
        or os.getenv("SECRET_KEY")
        or "fallback_secret_key_98765"
    )
    token = jwt.encode({"userId": user["id"]}, jwt_secret, algorithm="HS256")
    return jsonify({"token": token, "name": user["name"]})
