import os
from functools import wraps

import jwt
from dotenv import load_dotenv

# Добавили импорт 'g'
from flask import g, jsonify, request

# На всякий случай гарантируем загрузку .env и в этом модуле
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(base_dir, ".env"))


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Проверяем наличие токена в заголовках
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Токен отсутствует"}), 401

        try:
            # Безопасное получение ключа: если из .env пришел None, берем дефолтный фолбек
            jwt_secret = (
                os.getenv("JWT_SECRET")
                or os.getenv("SECRET_KEY")
                or "fallback_secret_key_98765"
            )

            # Декодируем токен
            data = jwt.decode(token, jwt_secret, algorithms=["HS256"])

            # В зависимости от того, как у тебя называется поле при генерации (userId или id)
            current_user_id = data.get("userId") or data.get("id")

            # СТРОГО ОБЯЗАТЕЛЬНО: записываем ID в глобальный контекст Flask,
            # чтобы profile.py (и другие роуты) могли его оттуда прочитать
            g.user_id = current_user_id

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Срок действия токена истек"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Неверный токен"}), 401
        except Exception as e:
            return jsonify({"message": f"Ошибка авторизации: {str(e)}"}), 401

        # Вызываем функцию БЕЗ передачи аргумента, так как роуты используют g.user_id
        return f(*args, **kwargs)

    return decorated
