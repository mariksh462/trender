import json
import os

DB_FILE = "users_db.json"


def load_users():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.decoder.JSONDecodeError:
            return {}
    return {}


def save_users(db):
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(db, file, ensure_ascii=False, indent=4)


def run_manual_analytics(username):
    """Проводить опитування користувача та рахує динаміку росту."""
    print(f"\n--- Щоденний звіт для @{username} ---")

    try:
        current_followers = int(input("1. Скільки у вас сьогодні підписників?: "))
        current_posts = int(input("2. Яка загальна кількість постів на акаунті?: "))
        avg_likes = int(input("3. Скільки лайків в середньому збирають останні пости?: "))
    except ValueError:
        print("❌ Помилка: потрібно вводити лише цифри. Аналітику скасовано.")
        return None

    db = load_users()

    # Якщо користувач новий — реєструємо
    if username not in db:
        print("\n[Система] Зберігаємо ці дані як вашу стартову точку...")
        db[username] = {
            "start_followers": current_followers,
            "start_posts": current_posts,
            "start_likes": avg_likes
        }
        save_users(db)

    # Рахуємо динаміку
    start_data = db[username]

    fol_diff = current_followers - start_data["start_followers"]
    posts_diff = current_posts - start_data["start_posts"]
    likes_diff = avg_likes - start_data["start_likes"]

    return {
        "username": username,
        "followers": {"current": current_followers, "diff": fol_diff},
        "posts": {"current": current_posts, "diff": posts_diff},
        "likes": {"current": avg_likes, "diff": likes_diff}
    }


def print_dashboard(data):
    """Виводить результати самоаналізу."""
    if not data:
        return

    def get_arrow(val):
        if val > 0:
            return f"⬆️ +{val:,}"
        elif val < 0:
            return f"⬇️ {val:,}"
        return "➡️ 0 (Без змін)"

    print(f"\n" + "=" * 45)
    print(f"📊 ВАШ РІСТ З МОМЕНТУ РЕЄСТРАЦІЇ: @{data['username']}")
    print("=" * 45)
    print(f"👥 Підписники:     {data['followers']['current']:,}")
    print(f"   Динаміка:       {get_arrow(data['followers']['diff'])}")
    print("-" * 45)
    print(f"📝 Кількість постів: {data['posts']['current']:,}")
    print(f"   Динаміка:         {get_arrow(data['posts']['diff'])}")
    print("-" * 45)
    print(f"❤️ Середні лайки:  {data['likes']['current']:,}")
    print(f"   Динаміка:       {get_arrow(data['likes']['diff'])}")
    print("=" * 45 + "\n")
