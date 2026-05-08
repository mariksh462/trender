from pytrends.request import TrendReq


def get_top_daily_trends():
    """Збирає загальні найпопулярніші пошукові тренди в Україні."""
    print("Збираю загальні топ-тренди Google для України...")

    try:
        pytrends = TrendReq(hl='uk-UA', tz=120)

        # Отримуємо список трендів для України
        trending_df = pytrends.trending_searches(pn='ukraine')

        if not trending_df.empty:
            # Дані повертаються в таблиці, беремо першу колонку і топ-5 рядків
            trends_list = trending_df[0].head(5).tolist()

            print("\n--- Найпопулярніші пошукові запити (з Google) ---")
            for i, trend in enumerate(trends_list, 1):
                print(f"{i}. {trend}")
            return trends_list
        else:
            print("Google не повернув трендів.")
            return []

    except Exception as e:
        print(f"\nПомилка Google Trends: {e}")
        print("Google тимчасово заблокував запит. Вмикаю систему резервних даних...")

        # Резервний набір загальнонаціональних трендів
        fallback_trends = [
            "штучний інтелект останні новини",
            "відключення світла графік",
            "курс долара",
            "нові технології",
            "кібербезпека"
        ]

        print("\n--- Резервні пошукові запити ---")
        for i, trend in enumerate(fallback_trends, 1):
            print(f"{i}. {trend}")

        return fallback_trends


# Тестовий запуск
if __name__ == "__main__":
    get_top_daily_trends()