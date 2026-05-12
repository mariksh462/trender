import random


def get_social_media_trends():
    """Бере актуальні формати з локальної бази SMM-трендів."""
    print("Завантажую актуальні формати з SMM-бази...")

    file_path = "trends_base.txt"

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # Читаємо всі непусті рядки
            all_trends = [line.strip() for line in file if line.strip()]

        if not all_trends:
            print("База трендів порожня. Додайте формати у trends_base.txt.")
            return []

        # Обираємо 3 випадкові тренди
        selected_trends = random.sample(all_trends, min(3, len(all_trends)))

        print("\n--- Обрані формати для генерації ---")
        for i, trend in enumerate(selected_trends, 1):
            print(f"{i}. {trend}")

        return selected_trends

    except FileNotFoundError:
        print(f"\n[Помилка] Файл '{file_path}' не знайдено.")
        print("Створіть його та запишіть туди актуальні меми/тренди.")
        return []


# Тестовий запуск
if __name__ == "__main__":
    get_social_media_trends()