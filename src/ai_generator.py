import json
import re

from database import save_idea
from trends_api import get_top_daily_trends

MODEL_PATH = "models/model.gguf"
_llm = None
_llm_error = None


def get_llm():
    """Load Llama model if available, otherwise return None."""
    global _llm, _llm_error

    if _llm_error is not None:
        return None
    
    if _llm is None:
        try:
            from llama_cpp import Llama
            _llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=4096,
                verbose=False,
            )
            print("✓ Llama model loaded")
        except FileNotFoundError:
            print(f"ℹ Model file not found: {MODEL_PATH}")
            _llm_error = "Model file not found"
            return None
        except Exception as e:
            print(f"ℹ LLM initialization error: {e}")
            _llm_error = str(e)
            return None

    return _llm


def _extract_first_json_object(raw_text):
    match = re.search(r"\{[\s\S]*\}", raw_text)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _format_idea_text(data):
    selected = data.get("selected_trends", [])
    if not isinstance(selected, list):
        selected = []

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        scenes = []

    hashtags = data.get("hashtags", [])
    if not isinstance(hashtags, list):
        hashtags = []

    selected_text = ", ".join(selected[:2]) if selected else "актуальні тренди"
    scene_lines = [f"{i+1}) {s}" for i, s in enumerate(scenes[:3])] or ["1) Короткий факт.", "2) Приклад для бренду.", "3) CTA."]
    tags_text = " ".join([t if str(t).startswith("#") else f"#{t}" for t in hashtags[:6]])
    if not tags_text:
        tags_text = "#тренди #контент #reels"

    return (
        f"Вибрані тренди: {selected_text}\n"
        f"Чому цей мікс простий: {data.get('why_simple', 'Теми вже в увазі аудиторії, тож їх легко подати через бренд.') }\n"
        f"Заголовок: {data.get('title', 'Ідея відео на базі актуальних трендів')}\n"
        f"Хук: {data.get('hook', 'За 20 секунд покажемо, як тренд перетворити у формат вашого бренду.')}\n"
        f"Сцени:\n" + "\n".join(scene_lines) + "\n"
        f"Візуал: {data.get('visual', 'Швидкі склейки, титри з фактами, 1-2 кадри продукту/послуги.')}\n"
        f"Хештеги: {tags_text}\n"
        f"CTA: {data.get('cta', 'Напиши в коментарях, який тренд розібрати наступним.')}"
    )


def _build_fallback_idea(top_trends, brand_profile):
    t1 = top_trends[0] if len(top_trends) > 0 else "актуальні новини"
    t2 = top_trends[1] if len(top_trends) > 1 else t1
    return (
        f"Вибрані тренди: {t1}, {t2}\n"
        f"Чому цей мікс простий: обидві теми вже в інформаційному полі, їх легко подати через приклад бренду.\n"
        f"Заголовок: Як {brand_profile} може використати тренди {t1} + {t2}\n"
        f"Хук: За 20 секунд покажемо, як тренд впливає на вашу нішу. "
        f"Перші 5 секунд - факт із тренду, далі - приклад для бренду.\n"
        f"Сцени:\n"
        f"1) Короткий факт про {t1}.\n"
        f"2) Приклад для бренду {brand_profile} на базі {t2}.\n"
        f"3) Підсумок: що зробити сьогодні, щоб використати тренд.\n"
        f"Візуал: великі титри, 2-3 швидкі склейки, один callout із цифрою/фактом.\n"
        f"Хештеги: #тренди #контент #маркетинг #reels #shorts\n"
        f"CTA: Напиши в коментарях, який тренд розібрати наступним."
    )


def _is_low_quality_output(text):
    required_markers = ["Заголовок:", "Хук:", "Сцени:", "CTA:"]
    if any(marker not in text for marker in required_markers):
        return True

    bad_markers = [
        "потрібно заповнити",
        "заповнити поля",
        "template",
        "placeholder",
        "для реалізації задачі",
    ]
    return any(marker in text.lower() for marker in bad_markers)


def generate_video_idea(brand_profile, save=True):
    """Генерує актуальну ідею відео на основі найпопулярнішого запиту з Google Trends
    та короткого опису бренду/профілю користувача (brand_profile — рядок).
    За замовчуванням просто повертає ідею; щоб зберегти в БД, передайте save=True.
    """
    try:
        trends = get_top_daily_trends()
        # Використовуємо кілька найпопулярніших трендів (до 5)
        top_trends = trends[:5] if trends else ["актуальні тренди"]

        print(f"Генерую ідею відео для бренду '{brand_profile}' на основі топ-трендів: {', '.join(top_trends)}...")

        trends_list_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(top_trends)])

        prompt = f'''### System:
    Ти — досвідчений контент-стратег і креатор відео для соцмереж. Пиши українською мовою.
    Поверни ТІЛЬКИ валідний JSON без пояснень і без markdown.
    JSON-схема:
    {{
      "selected_trends": ["string", "string"],
      "why_simple": "string",
      "title": "string",
      "hook": "string",
      "scenes": ["string", "string", "string"],
      "visual": "string",
      "hashtags": ["#tag1", "#tag2", "#tag3"],
      "cta": "string"
    }}
    Правила: не використовуй шаблонні фрази типу "потрібно заповнити поля"; дай готову практичну ідею.

    ### User:
    Бренд / профіль: {brand_profile}
    Найпопулярніші пошукові запити зараз (топ):
    {trends_list_text}
    Вибери 1-2 тренди і зроби просту унікальну ідею відео.

    ### Assistant:
    '''

        llm = get_llm()
        response = llm(
            prompt,
            max_tokens=420,
            temperature=0.45,
            top_p=0.95,
            stop=["### User:", "### System:"]
        )

        raw_text = response["choices"][0]["text"].strip()
        parsed = _extract_first_json_object(raw_text)

        if parsed:
            idea_text = _format_idea_text(parsed)
        else:
            idea_text = raw_text

        if _is_low_quality_output(idea_text):
            print("LLM output low quality -> using deterministic fallback idea.")
            idea_text = _build_fallback_idea(top_trends, brand_profile)

        print("\n--- Ідея відео ---")
        print(idea_text)
        print("------------------\n")

        # Витяг тегів із відповіді (слова що починаються з #)
        tags = " ".join([w for w in idea_text.split() if w.startswith("#")])
        if not tags:
            tags = "#video #trends"

        topic = f"Video idea (mixed trends) for {brand_profile}"
        if save:
            save_idea(topic, idea_text, tags)

        return idea_text

    except Exception as e:
        print(f"Помилка при генерації ідеї відео: {e}")
        return None


# Тестовий запуск (спрацює, якщо запускати саме цей файл)
if __name__ == "__main__":
    # Тест генерації ідеї відео на основі Google Trends і бренду (не зберігає в БД)
    sample_brand = "Сучасні IT сервіси"
    idea = generate_video_idea(sample_brand)
    print("Результат генерації ідеї відео:\n", idea)


def generate_video_idea_advanced(business_prompt, brand_description, target_audience_desc, 
                                 target_age_min, target_age_max):
    """Generates detailed video idea based on user's business profile."""
    try:
        trends = get_top_daily_trends()
        top_trends = trends[:8] if trends else ["trending topics"]
        age_range = f"{target_age_min}-{target_age_max} years old"

        # Try to use LLM first
        llm = get_llm()
        if llm:
            try:
                trends_list_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(top_trends)])
                prompt = f'''### System:
You are a professional SMM strategist. 
Generate a REAL, creative video idea for the user's business.
DO NOT use placeholder text like "Step 1" or "Video title". 
Write everything in Ukrainian.
Return ONLY valid JSON.

### User:
Business: {business_prompt}
Brand Description: {brand_description}
Target Audience: {target_audience_desc} (Age: {age_range})
Current Trends: {', '.join(top_trends[:3])}

### Assistant:
{{
  "title": "Конкретна назва ідеї",
  "description": "Детальний опис ідеї",
  "script": "[0-5] Хук; [5-15] Основна частина; [15-20] Заклик",
  "hook": "Реальна фраза для залучення уваги",
  "scenes": ["Опис сцени 1", "Опис сцени 2", "Опис сцени 3", "Опис сцени 4"],
  "visual_style": "Які кольори, який монтаж",
  "trending_topics": {json.dumps(top_trends[:3])},
  "target_audience_analysis": "Чому це спрацює для цієї аудиторії",
  "action_steps": ["Що зробити спочатку", "Як змонтувати", "Як опублікувати"],
  "hashtags": ["#тег1", "#тег2"],
  "cta": "Конкретний заклик до дії"
}}'''
                response = llm(prompt, max_tokens=1000, temperature=0.5, top_p=0.9)
                raw_text = response["choices"][0]["text"].strip()
                match = re.search(r"\{[\s\S]*\}", raw_text)
                if match:
                    parsed = json.loads(match.group(0))
                    print("✓ AI idea generated")
                    return parsed
            except Exception as e:
                print(f"ℹ LLM generation failed: {e}, using fallback")
        
        # Fallback - always works
        idea = {
            "title": f"Viral Video: Combine '{top_trends[0]}' with {brand_description}",
            "description": f"Use trending topic '{top_trends[0]}' to create engaging content for {target_audience_desc}. This trend has high engagement potential.",
            "script": f"[0-3] Hook with '{top_trends[0]}'; [3-10] Show how {business_prompt} solves a problem; [10-15] Demo/example; [15-20] CTA",
            "hook": f"Start with an eye-catching fact about {top_trends[0]} - grab attention in first 3 seconds",
            "scenes": [
                f"Scene 1: Introduce '{top_trends[0]}' trend or stat",
                f"Scene 2: Connect to {brand_description}",
                "Scene 3: Demonstrate value or solution",
                "Scene 4: Call-to-action and engagement prompt"
            ],
            "visual_style": "Fast-paced cuts, bright colors, text overlays for emphasis, trending audio/music, phone/camera quality is fine",
            "trending_topics": top_trends[:3],
            "target_audience_analysis": f"Your {age_range} audience responds to {', '.join(top_trends[:2])}. They share content that educates and entertains. This idea combines both.",
            "action_steps": [
                f"Step 1: Research recent examples of {top_trends[0]} content",
                f"Step 2: Write 30-second script explaining how {business_prompt} relates",
                "Step 3: Film 3-5 short clips with good lighting",
                "Step 4: Edit with trending sounds, post to all platforms",
                "Step 5: Respond to comments within first hour"
            ],
            "hashtags": ["#trending", "#viral", "#content", "#shorts", "#reels", f"#{top_trends[0].replace(' ', '')}"],
            "cta": "Follow for more ideas | Comment your thoughts | Share with your team"
        }
        print("✓ Fallback idea generated")
        return idea
        
    except Exception as e:
        print(f"Error in idea generation: {e}")
        # Ultimate fallback
        return {
            "title": "Video Content Idea",
            "description": "Create engaging short-form video content for your audience",
            "script": "[0-5] Attention grabber; [5-15] Main content; [15-20] Call to action",
            "hook": "Start with something surprising or valuable in first 3 seconds",
            "scenes": [
                "Scene 1: Hook/attention",
                "Scene 2: Value proposition",
                "Scene 3: Demonstration",
                "Scene 4: Call to action"
            ],
            "visual_style": "Professional but authentic, fast cuts, on-screen text, trending audio",
            "trending_topics": ["Video content", "Authentic marketing", "Short-form content"],
            "target_audience_analysis": "Your audience prefers authentic, valuable content that educates and entertains",
            "action_steps": [
                "Step 1: Plan your message",
                "Step 2: Record video clips",
                "Step 3: Edit and add effects",
                "Step 4: Post and engage with audience"
            ],
            "hashtags": ["#content", "#video", "#marketing", "#shorts"],
            "cta": "Follow for more content ideas"
        }