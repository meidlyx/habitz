import os

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS

base_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(base_dir, ".env"))

from backend.db.database import init_db

init_db()

from routes.achievements import achievements_bp
from routes.auth import auth_bp
from routes.habits import habits_bp
from routes.profile import profile_bp
from routes.tasks import tasks_bp

app = Flask(__name__, static_folder="../frontend")
CORS(app)

app.config["JSON_AS_ASCII"] = False

#! Регистрация всех Blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(habits_bp, url_prefix="/api/habits")
app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
app.register_blueprint(profile_bp, url_prefix="/api/profile")
app.register_blueprint(achievements_bp, url_prefix="/api/achievements")


#! Раздача статических файлов фронтенда
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "app.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
