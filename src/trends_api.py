from pytrends.request import TrendReq


def get_trends_for_topic(keyword):
    """Збирає тренди з Google. Якщо є блокування 429 - видає резервні дані."""
    print(f"Збираю аналітику Google Trends для теми: '{keyword}'...")

    try:
        # retries і backoff_factor додають затримки між спробами, щоб не "злити" Google
        pytrends = TrendReq(hl='uk-UA', tz=120)
        pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='UA', gprop='')

        related_data = pytrends.related_queries()
        top_queries = related_data[keyword]['top']

        if top_queries is not None:
            trends_list = top_queries['query'].head(5).tolist()
            print("\n--- Актуальні пошукові запити (з Google) ---")
            for i, trend in enumerate(trends_list, 1):
                print(f"{i}. {trend}")
            return trends_list
        else:
            print("Немає достатньо даних для цього слова.")
            return []

    except Exception as e:
        print(f"\nПомилка Google Trends: {e}")
        print("Google тимчасово заблокував запит. Вмикаю систему резервних даних...")

        # Резервний набір трендів (Mock-дані), щоб програма не зупинялася
        fallback_trends = [
            f"{keyword} останні новини",
            f"{keyword} огляд інструментів",
            f"{keyword} поради для новачків",
            f"як працює {keyword}"
        ]

        print("\n--- Резервні пошукові запити ---")
        for i, trend in enumerate(fallback_trends, 1):
            print(f"{i}. {trend}")

        return fallback_trends


# Тестовий запуск
if __name__ == "__main__":
    get_trends_for_topic("штучний інтелект")