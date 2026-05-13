from trends_api import get_social_media_trends
from ai_generator import generate_smm_ideas
from stats_analyzer import run_manual_analytics, print_dashboard


def run_smm_assistant():
    print("=== SMM Assistant v6.0 (Manual Analytics) ===")

    while True:
        print("\n=== Головне меню ===")
        print("1. Ввести статистику та переглянути ріст")
        print("2. Згенерувати ідеї для продукту")
        print("3. Вийти з програми")

        choice = input("\nОберіть дію (1-3): ")

        if choice == "1":
            username = input("\nВведіть ваш нікнейм (без @): ")
            stats = run_manual_analytics(username)
            print_dashboard(stats)

        elif choice == "2":
            user_input = input("\nЯкий продукт піаримо сьогодні?: ")
            current_trends = get_social_media_trends()
            if current_trends:
                generate_smm_ideas(user_input, current_trends)

        elif choice == "3":
            print("\nРоботу завершено. До побачення!")
            break

        else:
            print("Невідома команда. Введіть 1, 2 або 3.")


if __name__ == "__main__":
    run_smm_assistant()
