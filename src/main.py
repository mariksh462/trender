from trends_api import get_social_media_trends
from ai_generator import generate_smm_ideas
from stats_analyzer import register_user, get_dashboard_stats, print_dashboard


def run_smm_assistant():
    print("=== SMM Assistant v3.1 ===")
    print("Вітаємо! Для початку роботи авторизуйтесь у системі.\n")

    # 1. АВТОРИЗАЦІЯ (виконується лише один раз при старті)
    username = input("Введіть ваш нікнейм (без @): ")
    stats = get_dashboard_stats(username)

    if not stats:
        print(f"\n[Система] Профіль @{username} не знайдено в базі. Проходимо реєстрацію.")
        platform = input("Ваша соцмережа (instagram/tiktok): ")
        try:
            followers = int(input("Скільки у вас ЗАРАЗ підписників?: "))
            views = int(input("Скільки у вас ЗАРАЗ переглядів (в середньому)?: "))
        except ValueError:
            print("Помилка: потрібно вводити числа. Запустіть програму ще раз.")
            return

        register_user(username, platform, followers, views)
        print("\n✅ Дані успішно збережено!")
        stats = get_dashboard_stats(username)

    print_dashboard(stats)

    # 2. ГОЛОВНИЙ ЦИКЛ (користувач залишається в системі)
    while True:
        print("\n=== Головне меню ===")
        print("1. Згенерувати нові SMM-ідеї")
        print("2. Переглянути статистику (Дашборд)")
        print("3. Вийти з програми")

        choice = input("\nОберіть дію (1-3): ")

        if choice == "1":
            user_input = input("\nЯкий продукт піаримо сьогодні?: ")
            current_trends = get_social_media_trends()

            if not current_trends:
                print("Роботу зупинено: немає трендів для генерації.")
                continue  # Повертає в головне меню

            generate_smm_ideas(user_input, current_trends)

        elif choice == "2":
            stats = get_dashboard_stats(username)
            print_dashboard(stats)

        elif choice == "3":
            print(f"\nДякуємо за роботу, @{username}! До побачення.")
            break  # Вихід з циклу і закриття програми

        else:
            print("Невідома команда. Введіть цифру від 1 до 3.")


if __name__ == "__main__":
    run_smm_assistant()