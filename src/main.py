from trends_api import get_trends_for_topic
from ai_generator import generate_smm_post


def run_smm_assistant(base_topic):
    print("=== Запуск SMM Assistant ===\n")

    # Отримуємо тренд (або резервний варіант від Дзвінки)
    trends = get_trends_for_topic(base_topic)

    if not trends:
        print("Не вдалося отримати теми. Зупинка.")
        return

    # Беремо найперший запит зі списку
    top_trend = trends[0]
    print(f"\n[Система] Обрано тему для генерації: {top_trend}\n")

    # Передаємо тему в Ollama (модуль Лізи) і зберігаємо
    generate_smm_post(top_trend)

    print("\n=== Роботу завершено ===")


if __name__ == "__main__":
    run_smm_assistant("штучний інтелект")