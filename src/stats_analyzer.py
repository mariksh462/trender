import json
import os
import random

DB_FILE = "users_db.json"


def load_users():
    """Завантажує базу користувачів з файлу."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


def save_users(data):
    """Зберігає оновлену базу у файл."""
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def register_user(username, platform, followers, views):
    """Зберігає початкові (базові) метрики користувача."""
    db = load_users()
    db[username] = {
        "platform": platform,
        "base_followers": followers,
        "base_views": views
    }
    save_users(db)


def get_dashboard_stats(username):
    """Генерує статистику відносно збережених початкових даних."""
    db = load_users()
    if username not in db:
        return None  # Користувача ще немає в базі

    user_data = db[username]

    # Для MVP симулюємо оновлені дані (ніби пройшов час, і цифри виросли)
    # В майбутньому тут буде парсинг реальних поточних даних
    current_followers = int(user_data["base_followers"] * random.uniform(1.0, 1.08))
    current_views = int(user_data["base_views"] * random.uniform(1.0, 1.15))

    # Рахуємо різницю між тим, що було, і тим, що стало
    fol_diff = current_followers - user_data["base_followers"]
    views_diff = current_views - user_data["base_views"]

    return {
        "user": username,
        "platform": user_data["platform"],
        "followers": {"total": current_followers, "diff": fol_diff},
        "views": {"total": current_views, "diff": views_diff},
        "is_growing": fol_diff >= 0
    }


def print_dashboard(data):
    """Виводить дашборд."""

    def get_arrow(value):
        return f"⬆️ +{value:,}" if value > 0 else f"⬇️ {value:,}"

    print(f"\n" + "=" * 40)
    print(f"📊 ГОЛОВНИЙ ЕКРАН: @{data['user']} | {data['platform'].upper()}")
    print("=" * 40)
    print(f"👥 Підписники: {data['followers']['total']:,}")
    print(f"   Динаміка:   {get_arrow(data['followers']['diff'])}")
    print("-" * 40)
    print(f"👀 Перегляди:  {data['views']['total']:,}")
    print(f"   Динаміка:   {get_arrow(data['views']['diff'])}")
    print("=" * 40 + "\n")