from trends_api import get_social_media_trends
from ai_generator import generate_smm_ideas


def run_smm_assistant():
    print("=== SMM Assistant: Генератор Креативів ===\n")

    user_input = input("Який продукт піаримо? (наприклад: 'одяг', 'кав'ярня'): ")

    current_trends = get_social_media_trends()

    if not current_trends:
        print("Роботу зупинено: немає трендів для генерації.")
        return

    generate_smm_ideas(user_input, current_trends)

    print("\n=== Роботу завершено ===")


if __name__ == "__main__":
    run_smm_assistant()