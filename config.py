import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Admin user IDs (Telegram user_id as integers)
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip().isdigit()]

# Quiz settings
QUESTIONS_PER_QUIZ = 10       # Default questions per session
QUESTION_TIMEOUT = 30         # Seconds per question (0 = no limit)
STREAK_BONUS_THRESHOLD = 3    # Consecutive correct answers for bonus

# Points
POINTS_CORRECT = 10
POINTS_BONUS_STREAK = 5       # Extra points for streak

# Categories
DEFAULT_CATEGORIES = [
    "Жалпы білім",
    "Тарих",
    "Ғылым",
    "Технология",
    "Спорт",
    "Мәдениет",
]
