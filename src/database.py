import os
import psycopg2
from dotenv import load_dotenv

# Завантажуємо посилання на БД з файлу .env
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Створює та повертає підключення до бази даних."""
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"Помилка підключення до БД: {e}")
        return None


def create_table():
    """Створює таблицю для збереження згенерованих постів, якщо її ще немає."""
    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        # SQL-запит на створення таблиці
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smm_posts (
                id SERIAL PRIMARY KEY,
                topic VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Таблиця 'smm_posts' готова.")
    except Exception as e:
        print(f"Помилка створення таблиці: {e}")
    finally:
        cursor.close()
        conn.close()


def save_post(topic, content, tags):
    """Зберігає згенерований пост у базу."""
    conn = get_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO smm_posts (topic, content, tags)
            VALUES (%s, %s, %s);
        """, (topic, content, tags))
        conn.commit()
        print("Пост успішно збережено!")
    except Exception as e:
        print(f"Помилка збереження: {e}")
    finally:
        cursor.close()
        conn.close()


def get_all_posts():
    """Отримує всі збережені пости з бази даних."""
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        # Отримуємо всі пости, найновіші зверху
        cursor.execute("SELECT id, topic, content, tags, created_at FROM smm_posts ORDER BY created_at DESC;")
        posts = cursor.fetchall()

        for post in posts:
            print(f"ID: {post[0]} | Тема: {post[1]}")

        return posts
    except Exception as e:
        print(f"Помилка читання даних: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# Блок для перевірки коду
if __name__ == "__main__":
    print("--- Перевірка бази даних ---")
    # Викликаємо функцію читання
    all_posts = get_all_posts()

    if all_posts:
        print(f"\nУспішно знайдено постів: {len(all_posts)}")
    else:
        print("\nБаза поки порожня або сталася помилка.")

    # 2. Тестуємо запис даних (імітація роботи вашого ШІ)
    save_post(
        topic="Тренди IT 2026",
        content="Сьогодні розберемо головні новини у сфері штучного інтелекту...",
        tags="#IT #ШІ #новини"
    )