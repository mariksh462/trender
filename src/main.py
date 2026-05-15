import json
import os
import hashlib
import secrets
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from ai_generator import generate_video_idea_advanced
from database import create_table, get_user_by_username, register_user, save_user_profile, get_user_profile, save_idea, get_user_ideas, get_idea_by_id
from trends_api import get_top_daily_trends


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "FrontEnd")
HOST = "127.0.0.1"
PORT = 8000

# Простой session manager (в production використовувати Redis/DB)
user_sessions = {}


def hash_password(password):
    """Хешує пароль."""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"


def verify_password(password, hash_stored):
    """Перевіряє пароль."""
    try:
        salt, pwd_hash = hash_stored.split('$')
        pwd_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return pwd_check.hex() == pwd_hash
    except:
        return False


def get_session_token():
    """Генерує унікальний session token."""
    return secrets.token_urlsafe(32)


def extract_user_id_from_cookie(headers):
    """Витягує user_id з cookie."""
    cookies = headers.get('Cookie', '')
    for cookie in cookies.split(';'):
        if 'session_token=' in cookie:
            token = cookie.split('session_token=')[1].split(';')[0].strip()
            if token in user_sessions:
                return user_sessions[token]
    return None


class TrendIdeaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Cookie")
        self.send_header("Access-Control-Allow-Credentials", "true")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
            return super().do_GET()

        # API для трендів
        if self.path == "/api/trends":
            try:
                trends = get_top_daily_trends()
                self._send_json({"success": True, "trends": trends})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=HTTPStatus.BAD_GATEWAY)
            return

        # API для отримання профілю користувача
        if self.path == "/api/me":
            user_id = extract_user_id_from_cookie(self.headers)
            if not user_id:
                self._send_json({"success": False, "error": "Not authenticated"}, status=HTTPStatus.UNAUTHORIZED)
                return

            profile = get_user_profile(user_id)
            if profile:
                self._send_json({"success": True, "profile": profile})
            else:
                self._send_json({"success": True, "profile": None})
            return

        # API для отримання ідей користувача
        if self.path == "/api/ideas":
            user_id = extract_user_id_from_cookie(self.headers)
            if not user_id:
                self._send_json({"success": False, "error": "Not authenticated"}, status=HTTPStatus.UNAUTHORIZED)
                return

            ideas = get_user_ideas(user_id)
            self._send_json({"success": True, "ideas": ideas})
            return

        # API для отримання однієї ідеї
        if self.path.startswith("/api/ideas/"):
            idea_id = self.path.split("/")[-1]
            try:
                idea_id = int(idea_id)
                idea = get_idea_by_id(idea_id)
                if idea:
                    self._send_json({"success": True, "idea": idea})
                else:
                    self._send_json({"success": False, "error": "Idea not found"}, status=HTTPStatus.NOT_FOUND)
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=HTTPStatus.BAD_REQUEST)
            return

        return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(content_length) if content_length else b"{}"

        try:
            data = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON")
            return

        # Реєстрація
        if self.path == "/api/register":
            return self._handle_register(data)

        # Логін
        if self.path == "/api/login":
            return self._handle_login(data)

        # Логаут
        if self.path == "/api/logout":
            return self._handle_logout()

        # Збереження профілю
        if self.path == "/api/profile":
            return self._handle_save_profile(data)

        # Генерування ідеї
        if self.path == "/api/generate-idea":
            return self._handle_generate_idea(data)

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def _handle_register(self, data):
        """Реєстрація користувача."""
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        email = data.get("email", "").strip()

        if not username or not password:
            self._send_json(
                {"success": False, "error": "Username and password required"},
                status=HTTPStatus.BAD_REQUEST
            )
            return

        # Перевіримо, чи не існує користувач
        if get_user_by_username(username):
            self._send_json(
                {"success": False, "error": "User already exists"},
                status=HTTPStatus.CONFLICT
            )
            return

        # Реєструємо користувача
        user_id = register_user(username, hash_password(password), email)
        if user_id:
            # Створюємо сесію
            session_token = get_session_token()
            user_sessions[session_token] = user_id

            self._send_json(
                {
                    "success": True,
                    "message": "User registered successfully",
                    "user_id": user_id
                },
                status=HTTPStatus.CREATED,
                set_cookie=f"session_token={session_token}; Path=/; HttpOnly"
            )
        else:
            self._send_json(
                {"success": False, "error": "Registration failed"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def _handle_login(self, data):
        """Логіндження користувача."""
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            self._send_json(
                {"success": False, "error": "Username and password required"},
                status=HTTPStatus.BAD_REQUEST
            )
            return

        user = get_user_by_username(username)
        if not user or not verify_password(password, user["password"]):
            self._send_json(
                {"success": False, "error": "Invalid credentials"},
                status=HTTPStatus.UNAUTHORIZED
            )
            return

        # Створюємо сесію
        session_token = get_session_token()
        user_sessions[session_token] = user["id"]

        self._send_json(
            {
                "success": True,
                "message": "Logged in successfully",
                "user_id": user["id"],
                "profile_exists": get_user_profile(user["id"]) is not None
            },
            set_cookie=f"session_token={session_token}; Path=/; HttpOnly"
        )

    def _handle_logout(self):
        """Логаут користувача."""
        # Видаляємо cookie
        self._send_json(
            {"success": True, "message": "Logged out successfully"},
            set_cookie="session_token=; Path=/; HttpOnly; Max-Age=0"
        )

    def _handle_save_profile(self, data):
        """Збереження профілю користувача."""
        user_id = extract_user_id_from_cookie(self.headers)
        if not user_id:
            self._send_json(
                {"success": False, "error": "Not authenticated"},
                status=HTTPStatus.UNAUTHORIZED
            )
            return

        try:
            full_name = data.get("full_name", "").strip()
            age = data.get("age")
            business_name = data.get("business_name", "").strip()
            brand_description = data.get("brand_description", "").strip()
            business_prompt = data.get("business_prompt", "").strip()
            target_audience_desc = data.get("target_audience_desc", "").strip()
            target_age_min = data.get("target_audience_age_min", 18)
            target_age_max = data.get("target_audience_age_max", 65)
            platforms = data.get("platforms", [])

            if not full_name or not business_name:
                self._send_json(
                    {"success": False, "error": "Full name and business name are required"},
                    status=HTTPStatus.BAD_REQUEST
                )
                return

            success = save_user_profile(
                user_id, full_name, age, business_name, brand_description,
                business_prompt, target_audience_desc,
                target_age_min, target_age_max, platforms
            )

            if success:
                self._send_json({"success": True, "message": "Profile saved successfully"})
            else:
                self._send_json(
                    {"success": False, "error": "Failed to save profile"},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            self._send_json(
                {"success": False, "error": str(e)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def _handle_generate_idea(self, data):
        """Генерування ідеї для користувача."""
        user_id = extract_user_id_from_cookie(self.headers)
        if not user_id:
            self._send_json(
                {"success": False, "error": "Not authenticated"},
                status=HTTPStatus.UNAUTHORIZED
            )
            return

        try:
            # Отримуємо профіль користувача
            profile = get_user_profile(user_id)
            if not profile:
                self._send_json(
                    {"success": False, "error": "Profile not found. Please complete your profile first."},
                    status=HTTPStatus.BAD_REQUEST
                )
                return

            # Генеруємо ідею на основі профілю
            idea_data = generate_video_idea_advanced(
                profile["business_prompt"],
                profile["brand_description"],
                profile["target_audience_desc"],
                profile["target_audience_age_min"],
                profile["target_audience_age_max"]
            )

            if not idea_data:
                self._send_json(
                    {"success": False, "error": "Failed to generate idea"},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR
                )
                return

            # Зберігаємо ідею в БД
            idea_id = save_idea(
                user_id,
                idea_data.get("title", "Video Idea"),
                idea_data.get("description", ""),
                idea_data.get("script", ""),
                idea_data.get("hook", ""),
                json.dumps(idea_data.get("scenes", []), ensure_ascii=False),
                idea_data.get("visual_style", ""),
                json.dumps(idea_data.get("trending_topics", []), ensure_ascii=False),
                idea_data.get("target_audience_analysis", ""),
                json.dumps(idea_data.get("action_steps", []), ensure_ascii=False),
                " ".join(idea_data.get("hashtags", [])),
                idea_data.get("cta", "")
            )

            if idea_id:
                idea_data["id"] = idea_id
                self._send_json(
                    {"success": True, "idea": idea_data},
                    status=HTTPStatus.CREATED
                )
            else:
                self._send_json(
                    {"success": False, "error": "Failed to save idea"},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            print(f"Error generating idea: {e}")
            self._send_json(
                {"success": False, "error": str(e)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def _send_json(self, payload, status=HTTPStatus.OK, set_cookie=None):
        """Відправляє JSON відповідь."""
        def json_serial(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        body = json.dumps(payload, default=json_serial, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(body)


def main():
    """Запускає сервер."""
    create_table()
    
    server = ThreadingHTTPServer((HOST, PORT), TrendIdeaHandler)
    print(f"✓ Server running on http://{HOST}:{PORT}")
    print(f"✓ Open the dashboard page in your browser: http://{HOST}:{PORT}/dashboard.html")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        server.shutdown()


if __name__ == "__main__":
    main()
