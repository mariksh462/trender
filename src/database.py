import os
import json

_env_loaded = False


def _load_env_file():
    """Loads variables from src/.env if present and not already set in env."""
    global _env_loaded
    if _env_loaded:
        return

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        _env_loaded = True
        return

    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    finally:
        _env_loaded = True


def _build_local_database_url():
    host = os.getenv("PGHOST", "127.0.0.1")
    port = os.getenv("PGPORT", "5432")
    db_name = os.getenv("PGDATABASE", "trender")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "123")
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_connection():
    _load_env_file()
    
    # Тимчасово пропишіть пряме підключення для перевірки:
    db_url = "postgresql://postgres:123@127.0.0.1:5432/trender"

    try:
        import psycopg
        conn = psycopg.connect(db_url)
        print("PostgreSQL connection established")
        return conn
    except Exception as e:
        print(f"ERROR: Cannot connect to PostgreSQL: {e}")
        return None


def create_table():
    """Створює таблиці для повної роботи додатку."""
    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER UNIQUE,
                full_name VARCHAR(255),
                age INTEGER,
                business_name VARCHAR(255),
                brand_description TEXT,
                business_prompt TEXT,
                target_audience_desc TEXT,
                target_audience_age_min INTEGER,
                target_audience_age_max INTEGER,
                platforms_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smm_ideas (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                script TEXT,
                hook TEXT,
                scenes TEXT,
                visual_style TEXT,
                trending_topics TEXT,
                target_audience_analysis TEXT,
                action_steps TEXT,
                hashtags TEXT,
                cta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)

        conn.commit()
        print("✓ Таблиці готові до роботи.")
    except Exception as e:
        print(f"Помилка створення таблиць: {e}")
    finally:
        conn.close()


# ==================== USER FUNCTIONS ====================

def register_user(username, password, email=None):
    """Реєструє нового користувача."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (%s, %s, %s) RETURNING id",
            (username, password, email)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✓ Користувач '{username}' успішно зареєстрований!")
        return user_id
    except Exception as e:
        print(f"Помилка реєстрації: {e}")
        return None
    finally:
        conn.close()


def get_user_by_username(username):
    """Отримує користувача за ім'ям."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, email FROM users WHERE username = %s", (username,))
        
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "username": row[1],
            "password": row[2],
            "email": row[3]
        }
    except Exception as e:
        print(f"Помилка пошуку користувача: {e}")
        return None
    finally:
        conn.close()


# ==================== PROFILE FUNCTIONS ====================

def save_user_profile(user_id, full_name, age, business_name, brand_description, 
                      business_prompt, target_audience_desc, target_age_min, target_age_max, platforms):
    """Зберігає або оновлює профіль користувача."""
    conn = get_connection()
    if not conn:
        return False

    try:
        platforms_json = json.dumps(platforms, ensure_ascii=False) if isinstance(platforms, list) else platforms
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_profiles
            (user_id, full_name, age, business_name, brand_description,
             business_prompt, target_audience_desc,
             target_audience_age_min, target_audience_age_max, platforms_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET
                full_name = EXCLUDED.full_name,
                age = EXCLUDED.age,
                business_name = EXCLUDED.business_name,
                brand_description = EXCLUDED.brand_description,
                business_prompt = EXCLUDED.business_prompt,
                target_audience_desc = EXCLUDED.target_audience_desc,
                target_audience_age_min = EXCLUDED.target_audience_age_min,
                target_audience_age_max = EXCLUDED.target_audience_age_max,
                platforms_json = EXCLUDED.platforms_json,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, full_name, age, business_name, brand_description,
              business_prompt, target_audience_desc,
              target_age_min, target_age_max, platforms_json))
        
        conn.commit()
        print(f"✓ Профіль користувача успішно збережено!")
        return True
    except Exception as e:
        print(f"Помилка збереження профілю: {e}")
        return False
    finally:
        conn.close()


def get_user_profile(user_id):
    """Отримує профіль користувача за ID."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, full_name, age, business_name, brand_description,
                   business_prompt, target_audience_desc,
                   target_audience_age_min, target_audience_age_max,
                   platforms_json, created_at, updated_at
            FROM user_profiles WHERE user_id = %s
        """, (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return None

        platforms = json.loads(row[10]) if row[10] else []
        return {
            "id": row[0],
            "user_id": row[1],
            "full_name": row[2],
            "age": row[3],
            "business_name": row[4],
            "brand_description": row[5],
            "business_prompt": row[6],
            "target_audience_desc": row[7],
            "target_audience_age_min": row[8],
            "target_audience_age_max": row[9],
            "platforms": platforms,
            "created_at": row[11].isoformat() if row[11] else None, # Додаємо .isoformat()
            "updated_at": row[12].isoformat() if row[12] else None  # Додаємо .isoformat()
        }
    except Exception as e:
        print(f"Помилка отримання профілю: {e}")
        return None
    finally:
        conn.close()


# ==================== IDEAS FUNCTIONS ====================

def save_idea(user_id, title, description, script, hook, scenes, visual_style,
              trending_topics, target_audience_analysis, action_steps, hashtags, cta):
    """Зберігає згенеровану ідею."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO smm_ideas
            (user_id, title, description, script, hook, scenes, visual_style,
             trending_topics, target_audience_analysis, action_steps, hashtags, cta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (user_id, title, description, script, hook, scenes, visual_style,
              trending_topics, target_audience_analysis, action_steps, hashtags, cta))
        idea_id = cursor.fetchone()[0]
        
        conn.commit()
        print(f"✓ Ідея успішно збережена!")
        return idea_id
    except Exception as e:
        print(f"Помилка збереження ідеї: {e}")
        return None
    finally:
        conn.close()


def get_user_ideas(user_id):
    """Отримує всі ідеї користувача."""
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, title, description, script, hook, scenes, visual_style,
                   trending_topics, target_audience_analysis, action_steps, hashtags, cta, created_at
            FROM smm_ideas WHERE user_id = %s ORDER BY created_at DESC
        """, (user_id,))
        
        rows = cursor.fetchall()
        ideas = []

        for row in rows:
            idea = {
                "id": row[0],
                "title": row[2],
                "description": row[3],
                "script": row[4],
                "hook": row[5],
                "scenes": row[6],
                "visual_style": row[7],
                "trending_topics": row[8],
                "target_audience_analysis": row[9],
                "action_steps": row[10],
                "hashtags": row[11],
                "cta": row[12],
                "created_at": row[13].isoformat() if row[13] else None
            }
            ideas.append(idea)
        return ideas
    except Exception as e:
        print(f"Помилка отримання ідей: {e}")
        return []
    finally:
        conn.close()


def get_idea_by_id(idea_id):
    """Отримує ідею за ID."""
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, title, description, script, hook, scenes, visual_style,
                   trending_topics, target_audience_analysis, action_steps, hashtags, cta, created_at
            FROM smm_ideas WHERE id = %s
        """, (idea_id,))
        
        row = cursor.fetchone()
        if not row:
            return None

        return {
            "id": row[0],
            "title": row[2],
            "description": row[3],
            "script": row[4],
            "hook": row[5],
            "scenes": row[6],
            "visual_style": row[7],
            "trending_topics": row[8],
            "target_audience_analysis": row[9],
            "action_steps": row[10],
            "hashtags": row[11],
            "cta": row[12],
            "created_at": row[13]
        }
    except Exception as e:
        print(f"Помилка отримання ідеї: {e}")
        return None
    finally:
        conn.close()


if __name__ == "__main__":
    print("Database module ready!")
