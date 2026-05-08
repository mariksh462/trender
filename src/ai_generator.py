import ollama
from database import save_post


def generate_smm_post(topic):
    """Генерує пост через локальну Ollama та передає на збереження в БД."""
    print(f"Генерую пост на тему: '{topic}'... (це може зайняти кілька секунд)")

    prompt = f"Напиши короткий пост для соцмереж про: {topic}"

    try:
        # Звернення до локальної моделі llama3
        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'system',
                'content': 'Ти досвідчений SMM-менеджер. Пиши тексти українською мовою. Структуруй текст абзацами, використовуй емодзі. В кінці завжди додавай заклик до дії (CTA).'
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ])

        # Витягуємо згенерований текст з відповіді
        generated_text = response['message']['content']

        print("\n--- Готовий текст ---")
        print(generated_text)
        print("---------------------\n")

        # Витягуємо хештеги зі згенерованого тексту
        tags = " ".join([word for word in generated_text.split() if word.startswith("#")])

        # Якщо ШІ не згенерував хештеги, ставимо дефолтні
        if not tags:
            tags = "#IT #trends"

        # Передаємо всі три потрібні аргументи у базу даних
        save_post(topic, generated_text, tags)

    except Exception as e:
        print(f"Сталася помилка при генерації: {e}")


# Тестовий запуск (спрацює, якщо запускати саме цей файл)
if __name__ == "__main__":
    generate_smm_post("Тренди IT 2026")