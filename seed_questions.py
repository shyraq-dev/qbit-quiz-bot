"""
Деректер базасына үлгі сұрақтар қосу скрипті.
Іске қосу: python seed_questions.py
"""
import asyncio
import sys
import os
import aiosqlite

# database.py-дан init_db импорттау үшін project root-ты path-қа қосамыз
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import init_db

DB_PATH = "qbit_quiz.db"

SAMPLE_QUESTIONS = [
    # ── Жалпы білім ──
    {
        "category": "Жалпы білім",
        "question": "Қазақстан Республикасының астанасы қандай қала?",
        "option_a": "Алматы", "option_b": "Астана",
        "option_c": "Шымкент", "option_d": "Қарағанды",
        "correct": "B", "difficulty": "easy",
    },
    {
        "category": "Жалпы білім",
        "question": "Жер шары Күннің айналасын қанша уақытта айналып шығады?",
        "option_a": "24 сағат", "option_b": "30 күн",
        "option_c": "365 күн", "option_d": "100 жыл",
        "correct": "C", "difficulty": "easy",
    },
    {
        "category": "Жалпы білім",
        "question": "Адам денесінде неше сүйек бар?",
        "option_a": "106", "option_b": "206",
        "option_c": "306", "option_d": "406",
        "correct": "B", "difficulty": "medium",
    },
    # ── Тарих ──
    {
        "category": "Тарих",
        "question": "Қазақ хандығы қай жылы құрылды?",
        "option_a": "1218 жыл", "option_b": "1465 жыл",
        "option_c": "1731 жыл", "option_d": "1991 жыл",
        "correct": "B", "difficulty": "medium",
    },
    {
        "category": "Тарих",
        "question": "Абылай хан қай ғасырда өмір сүрді?",
        "option_a": "XV ғасыр", "option_b": "XVI ғасыр",
        "option_c": "XVIII ғасыр", "option_d": "XIX ғасыр",
        "correct": "C", "difficulty": "medium",
    },
    {
        "category": "Тарих",
        "question": "Қазақстан тәуелсіздікті қай жылы алды?",
        "option_a": "1989", "option_b": "1990",
        "option_c": "1991", "option_d": "1992",
        "correct": "C", "difficulty": "easy",
    },
    # ── Ғылым ──
    {
        "category": "Ғылым",
        "question": "Судың химиялық формуласы қандай?",
        "option_a": "CO₂", "option_b": "NaCl",
        "option_c": "H₂O", "option_d": "O₂",
        "correct": "C", "difficulty": "easy",
    },
    {
        "category": "Ғылым",
        "question": "Жарықтың вакуумдағы жылдамдығы шамамен қанша?",
        "option_a": "300 км/с", "option_b": "3 000 км/с",
        "option_c": "30 000 км/с", "option_d": "300 000 км/с",
        "correct": "D", "difficulty": "medium",
    },
    {
        "category": "Ғылым",
        "question": "Периодтық жүйеде алтынның белгісі қандай?",
        "option_a": "Al", "option_b": "Ag",
        "option_c": "Au", "option_d": "At",
        "correct": "C", "difficulty": "medium",
    },
    # ── Технология ──
    {
        "category": "Технология",
        "question": "WWW дегеніміз не?",
        "option_a": "World Wide Web", "option_b": "World Wide Window",
        "option_c": "Wide World Web", "option_d": "Web World Wide",
        "correct": "A", "difficulty": "easy",
    },
    {
        "category": "Технология",
        "question": "Python қай жылы жасалды?",
        "option_a": "1985", "option_b": "1991",
        "option_c": "1999", "option_d": "2005",
        "correct": "B", "difficulty": "medium",
    },
    {
        "category": "Технология",
        "question": "1 гигабайт (GB) неше мегабайт (MB)?",
        "option_a": "100 MB", "option_b": "512 MB",
        "option_c": "1024 MB", "option_d": "2048 MB",
        "correct": "C", "difficulty": "medium",
    },
    # ── Спорт ──
    {
        "category": "Спорт",
        "question": "Олимпиада ойындары қанша жылда бір өткізіледі?",
        "option_a": "2 жыл", "option_b": "4 жыл",
        "option_c": "5 жыл", "option_d": "10 жыл",
        "correct": "B", "difficulty": "easy",
    },
    {
        "category": "Спорт",
        "question": "Футбол матчінде негізгі уақыт қанша минут?",
        "option_a": "60", "option_b": "80",
        "option_c": "90", "option_d": "120",
        "correct": "C", "difficulty": "easy",
    },
    # ── Мәдениет ──
    {
        "category": "Мәдениет",
        "question": "Абай Құнанбайұлы нені жазды?",
        "option_a": "«Манас»", "option_b": "«Қара сөздер»",
        "option_c": "«Шахнаме»", "option_d": "«Ромео мен Джульетта»",
        "correct": "B", "difficulty": "easy",
    },
    {
        "category": "Мәдениет",
        "question": "Домбыра — бұл не?",
        "option_a": "Ұрмалы аспап", "option_b": "Үрмелі аспап",
        "option_c": "Ішекті аспап", "option_d": "Электронды аспап",
        "correct": "C", "difficulty": "easy",
    },
]


async def seed():
    # Алдымен кестелерді жасаймыз (бұрын жоқ болса)
    await init_db()

    added = 0
    skipped = 0
    async with aiosqlite.connect(DB_PATH) as db:
        for q in SAMPLE_QUESTIONS:
            # Бірдей сұрақ қайта қосылмасын
            async with db.execute(
                "SELECT id FROM questions WHERE question = ?", (q["question"],)
            ) as cur:
                exists = await cur.fetchone()
            if exists:
                skipped += 1
                continue

            await db.execute(
                """INSERT INTO questions
                   (category, question, option_a, option_b, option_c, option_d,
                    correct, difficulty, approved)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    q["category"], q["question"],
                    q["option_a"], q["option_b"],
                    q["option_c"], q["option_d"],
                    q["correct"], q["difficulty"],
                ),
            )
            added += 1
        await db.commit()

    print(f"✅ {added} сұрақ қосылды!")
    if skipped:
        print(f"⏭️  {skipped} сұрақ бұрын қосылған, өткізілді.")


if __name__ == "__main__":
    asyncio.run(seed())