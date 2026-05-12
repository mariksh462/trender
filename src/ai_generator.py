import ollama
from database import save_post

def generate_smm_ideas(user_request, trends_list):
    """Генерує ідеї на основі запиту та списку трендів."""
    print(f"\nГенерую стратегію для: '{user_request}'...")

    trends_str = ", ".join(trends_list)

    # Додали жорстку вимогу щодо української мови в кінці промпту
    prompt = (
        f"Клієнт хоче розпіарити продукт: '{user_request}'. "
        f"Зараз у соцмережах популярні такі тренди: {trends_str}. "
        "Придумай 3 креативні ідеї для відео в TikTok чи Instagram, які поєднають продукт клієнта з цими трендами. "
        "УВАГА: Напиши всю відповідь ВИКЛЮЧНО українською мовою. Переклади всі ідеї українською."
    )

    try:
        response = ollama.chat(model='llama3', messages=[
            {
                'role': 'system',
                # Кардинально посилили системне правило
                'content': 'Ти креативний український SMM-стратег. Твоє найголовніше правило: ти генеруєш тексти ТІЛЬКИ українською мовою. Ніколи не використовуй англійську. Пиши чітко, практично. Описуй ідеї маркованим списком. В кінці додай 3-5 хештегів.'
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ])

        generated_text = response['message']['content']

        print("\n--- Згенеровані ідеї ---")
        print(generated_text)
        print("------------------------\n")

        tags = " ".join([word for word in generated_text.split() if word.startswith("#")])
        if not tags:
            tags = "#smm #тренди #просування"

        save_post(user_request, generated_text, tags)

    except Exception as e:
        print(f"Помилка ШІ: {e}")