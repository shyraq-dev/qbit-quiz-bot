import aiosqlite
import logging
from datetime import datetime
from typing import Optional

DB_PATH = "qbit_quiz.db"
logger = logging.getLogger(__name__)


async def init_db():
    """Initialize all database tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,                                                              username    TEXT,
                full_name   TEXT,
                total_score INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                wrong_answers   INTEGER DEFAULT 0,
                current_streak  INTEGER DEFAULT 0,
                best_streak     INTEGER DEFAULT 0,
                last_played     TEXT,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS questions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT NOT NULL,
                question    TEXT NOT NULL,
                option_a    TEXT NOT NULL,
                option_b    TEXT NOT NULL,
                option_c    TEXT NOT NULL,
                option_d    TEXT NOT NULL,
                correct     TEXT NOT NULL CHECK(correct IN ('A','B','C','D')),
                difficulty  TEXT DEFAULT 'medium' CHECK(difficulty IN ('easy','medium','hard')),
                added_by    INTEGER,
                approved    INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                category    TEXT,
                score       INTEGER DEFAULT 0,
                correct     INTEGER DEFAULT 0,
                wrong       INTEGER DEFAULT 0,
                total_q     INTEGER DEFAULT 0,
                streak      INTEGER DEFAULT 0,
                started_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)                                            );

            CREATE TABLE IF NOT EXISTS pending_questions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_by INTEGER NOT NULL,
                category    TEXT NOT NULL,
                question    TEXT NOT NULL,
                option_a    TEXT NOT NULL,
                option_b    TEXT NOT NULL,
                option_c    TEXT NOT NULL,
                option_d    TEXT NOT NULL,
                correct     TEXT NOT NULL,
                difficulty  TEXT DEFAULT 'medium',
                status      TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
                reviewed_by INTEGER,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_questions_category ON questions(category, approved);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON game_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_users_score ON users(total_score DESC);

            -- ═══ Quiz Settings (v1.2) ═══

            -- Глобалды баптаулар (бот иесі)
            CREATE TABLE IF NOT EXISTS bot_settings (
                id              INTEGER PRIMARY KEY DEFAULT 1 CHECK(id = 1),
                default_questions_count INTEGER DEFAULT 15,
                default_time_limit      INTEGER DEFAULT 30,
                max_answer_options      INTEGER DEFAULT 4,
                max_correct_answers     INTEGER DEFAULT 1,
                shuffle_questions       INTEGER DEFAULT 1,
                shuffle_answers         INTEGER DEFAULT 1
            );

            -- Әдепкі мәндерді енгізу
            INSERT OR IGNORE INTO bot_settings (id) VALUES (1);

            -- Нұсқалар (variants)
            CREATE TABLE IF NOT EXISTS variants (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,                                            category        TEXT NOT NULL,
                variant_number  INTEGER NOT NULL,                                                             name            TEXT NOT NULL,
                description     TEXT,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, variant_number)
            );

            -- Қолданушы баптаулары
            CREATE TABLE IF NOT EXISTS user_quiz_settings (
                user_id         INTEGER PRIMARY KEY,
                questions_count INTEGER,
                time_limit      INTEGER,
                shuffle_questions INTEGER,
                shuffle_answers   INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_variants_category ON variants(category);

            -- ═══ ҰБТ режимі (v1.4) ═══

            -- ҰБТ пәндері
            CREATE TABLE IF NOT EXISTS ubt_subjects (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL UNIQUE,
                is_mandatory    INTEGER DEFAULT 0,
                questions_count INTEGER DEFAULT 25,
                time_minutes    INTEGER DEFAULT 45,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Міндетті пәндерді қосу (егер жоқ болса)
            INSERT OR IGNORE INTO ubt_subjects (name, is_mandatory) VALUES
                ('Математикалық сауаттылық', 1),
                ('Оқу сауаттылығы', 1),
                ('Қазақстан тарихы', 1);

            -- ҰБТ тақырыптар (пән ішінде)
            CREATE TABLE IF NOT EXISTS ubt_topics (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id  INTEGER NOT NULL,
                name        TEXT NOT NULL,
                created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(subject_id) REFERENCES ubt_subjects(id),
                UNIQUE(subject_id, name)
            );

            -- ҰБТ СҰРАҚТАРЫ (Quiz-ден БӨЛЕК!)
            CREATE TABLE IF NOT EXISTS ubt_questions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id      INTEGER NOT NULL,
                question_type   TEXT DEFAULT 'simple' CHECK(question_type IN ('simple','context','matching','multiple')),
                question_text   TEXT NOT NULL,
                context_text    TEXT,

                -- Simple/Context үшін (A,B,C,D)
                option_a        TEXT,
                option_b        TEXT,
                option_c        TEXT,
                option_d        TEXT,
                correct         TEXT,

                -- Matching үшін (JSON)
                matching_left   TEXT,
                matching_right  TEXT,
                matching_answer TEXT,

                -- Multiple үшін
                correct_multiple TEXT,

                image_url       TEXT,
                difficulty      TEXT DEFAULT 'medium',
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(subject_id) REFERENCES ubt_subjects(id)
            );

            CREATE INDEX IF NOT EXISTS idx_ubt_questions_subject ON ubt_questions(subject_id);
            CREATE INDEX IF NOT EXISTS idx_ubt_questions_type ON ubt_questions(question_type);

            -- ҰБТ сессиялары
            CREATE TABLE IF NOT EXISTS ubt_sessions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                mode            TEXT NOT NULL CHECK(mode IN ('full','quick')),
                mandatory_subjects TEXT,
                elective_subjects  TEXT,
                total_score     INTEGER DEFAULT 0,
                max_score       INTEGER DEFAULT 140,
                started_at      TEXT DEFAULT CURRENT_TIMESTAMP,
                finished_at     TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            );

            -- ҰБТ сессия нәтижелері (пән бойынша)
            CREATE TABLE IF NOT EXISTS ubt_results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  INTEGER NOT NULL,
                subject_id  INTEGER NOT NULL,
                score       INTEGER DEFAULT 0,
                correct     INTEGER DEFAULT 0,
                wrong       INTEGER DEFAULT 0,
                skipped     INTEGER DEFAULT 0,
                FOREIGN KEY(session_id) REFERENCES ubt_sessions(id),
                FOREIGN KEY(subject_id) REFERENCES ubt_subjects(id)
            );
                                                           CREATE INDEX IF NOT EXISTS idx_ubt_sessions_user ON ubt_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_ubt_results_session ON ubt_results(session_id);

            -- ═══ Broadcast (v1.7) ═══

            -- Хат жіберу тарихы
            CREATE TABLE IF NOT EXISTS broadcasts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id        INTEGER NOT NULL,
                message_text    TEXT NOT NULL,
                message_type    TEXT DEFAULT 'text' CHECK(message_type IN ('text','photo','video','document')),
                media_url       TEXT,
                target_type     TEXT DEFAULT 'all' CHECK(target_type IN ('all','active','inactive')),
                total_users     INTEGER DEFAULT 0,
                sent_count      INTEGER DEFAULT 0,
                failed_count    INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT CURRENT_TIMESTAMP,                                               finished_at     TEXT
            );
                                                           CREATE INDEX IF NOT EXISTS idx_broadcasts_admin ON broadcasts(admin_id);
        """)
        await db.commit()
                                                       # Link questions to UBT topics
        async with db.execute("PRAGMA table_info(questions)") as cur:
            columns = [row[1] for row in await cur.fetchall()]

        if 'variant_id' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN variant_id INTEGER REFERENCES variants(id)")
        if 'option_e' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN option_e TEXT")
        if 'option_f' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN option_f TEXT")
        if 'answer_options_count' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN answer_options_count INTEGER DEFAULT 4")
        if 'correct_count' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN correct_count INTEGER DEFAULT 1")
        if 'ubt_topic_id' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN ubt_topic_id INTEGER REFERENCES ubt_topics(id)")
        if 'image_url' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN image_url TEXT")
        if 'context_text' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN context_text TEXT")

        # Migration: Remove CHECK constraint from 'correct' column
        # Check if migration needed
        async with db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='questions'") as cur:
            row = await cur.fetchone()
            if row:
                table_sql = row[0]

                if "CHECK(correct IN ('A','B','C','D'))" in table_sql:
                    # Recreate table without CHECK constraint
                    await db.execute("""
                        CREATE TABLE questions_temp (
                            id          INTEGER PRIMARY KEY AUTOINCREMENT,
                            category    TEXT NOT NULL,
                            question    TEXT NOT NULL,                                                                    option_a    TEXT NOT NULL,                                                                    option_b    TEXT NOT NULL,                                                                    option_c    TEXT NOT NULL,                                                                    option_d    TEXT NOT NULL,                                                                    option_e    TEXT,
                            option_f    TEXT,
                            correct     TEXT NOT NULL,
                            difficulty  TEXT DEFAULT 'medium' CHECK(difficulty IN ('easy','medium','hard')),
                            added_by    INTEGER,
                            approved    INTEGER DEFAULT 0,
                            context_text TEXT,
                            image_url   TEXT,
                            variant_id  INTEGER,
                            answer_options_count INTEGER DEFAULT 4,
                            correct_count INTEGER DEFAULT 1,
                            ubt_topic_id INTEGER,
                            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

                    # Copy data
                    await db.execute("""
                        INSERT INTO questions_temp
                        SELECT * FROM questions
                    """)

                    # Drop old, rename new
                    await db.execute("DROP TABLE questions")
                    await db.execute("ALTER TABLE questions_temp RENAME TO questions")

        await db.commit()
        if 'question_type' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN question_type TEXT DEFAULT 'single' CHECK(question_type IN ('single','context','matching','multiple'))")
        if 'points' not in columns:
            await db.execute("ALTER TABLE questions ADD COLUMN points INTEGER DEFAULT 1")

        await db.commit()

        # Add shuffle columns to bot_settings          async with db.execute("PRAGMA table_info(bot_settings)") as cur:
            bot_cols = [row[1] for row in await cur.fetchall()]

        if 'shuffle_questions' not in bot_cols:
            await db.execute("ALTER TABLE bot_settings ADD COLUMN shuffle_questions INTEGER DEFAULT 1")
        if 'shuffle_answers' not in bot_cols:
            await db.execute("ALTER TABLE bot_settings ADD COLUMN shuffle_answers INTEGER DEFAULT 1")

        # Add feedback group settings
        if 'feedback_group_id' not in bot_cols:            await db.execute("ALTER TABLE bot_settings ADD COLUMN feedback_group_id INTEGER")         if 'feedback_topic_suggestion' not in bot_cols:
            await db.execute("ALTER TABLE bot_settings ADD COLUMN feedback_topic_suggestion INTEGER")
        if 'feedback_topic_complaint' not in bot_cols:
            await db.execute("ALTER TABLE bot_settings ADD COLUMN feedback_topic_complaint INTEGER")
        if 'feedback_topic_bug' not in bot_cols:
            await db.execute("ALTER TABLE bot_settings ADD COLUMN feedback_topic_bug INTEGER")
        if 'feedback_topic_contact' not in bot_cols:
            await db.execute("ALTER TABLE bot_settings ADD COLUMN feedback_topic_contact INTEGER")
                                                       # Add shuffle columns to user_quiz_settings
        async with db.execute("PRAGMA table_info(user_quiz_settings)") as cur:
            user_cols = [row[1] for row in await cur.fetchall()]

        if 'shuffle_questions' not in user_cols:
            await db.execute("ALTER TABLE user_quiz_settings ADD COLUMN shuffle_questions INTEGER")
        if 'shuffle_answers' not in user_cols:
            await db.execute("ALTER TABLE user_quiz_settings ADD COLUMN shuffle_answers INTEGER")

        # Add missing columns to ubt_sessions
        async with db.execute("PRAGMA table_info(ubt_sessions)") as cur:
            ubt_cols = [row[1] for row in await cur.fetchall()]

        if 'session_type' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN session_type TEXT DEFAULT 'full' CHECK(session_type IN ('full','short'))")
        if 'mandatory_score' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN mandatory_score INTEGER DEFAULT 0")                                                if 'elective1_id' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN elective1_id INTEGER")
        if 'elective1_score' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN elective1_score INTEGER DEFAULT 0")
        if 'elective2_id' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN elective2_id INTEGER")
        if 'elective2_score' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN elective2_score INTEGER DEFAULT 0")
        if 'total_correct' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN total_correct INTEGER DEFAULT 0")
        if 'total_wrong' not in ubt_cols:
            await db.execute("ALTER TABLE ubt_sessions ADD COLUMN total_wrong INTEGER DEFAULT 0")

        await db.commit()
        logger.info("Database initialized with ҰБТ реформа v1.8.")


# ─── USER ────────────────────────────────────────────────────────────────────

async def get_or_create_user(user_id: int, username: str, full_name: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row         
        # Try INSERT first with OR IGNORE (handles race condition)
        await db.execute(
            """INSERT OR IGNORE INTO users (user_id, username, full_name)
               VALUES (?, ?, ?)""",
            (user_id, username, full_name),
        )
        await db.commit()

        # Then SELECT the user (whether just created or already existed)
        async with db.execute(                             "SELECT * FROM users WHERE user_id = ?", (user_id,)                                       ) as cur:
            row = await cur.fetchone()

        return dict(row) if row else {}


async def update_user_stats(user_id: int, score: int, correct: int, wrong: int, streak: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users SET
                total_score    = total_score + ?,
                games_played   = games_played + 1,
                correct_answers = correct_answers + ?,
                wrong_answers  = wrong_answers + ?,
                current_streak = ?,
                best_streak    = MAX(best_streak, ?),
                last_played    = ?
               WHERE user_id = ?""",
            (score, correct, wrong, streak, streak, datetime.now().isoformat(), user_id),
        )
        await db.commit()
                                               
async def get_user_stats(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)                                       ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None


# ─── LEADERBOARD ─────────────────────────────────────────────────────────────

async def get_leaderboard(limit: int = 10) -> list[dict]:                                         async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT user_id, full_name, username, total_score,
                      games_played, best_streak,                                                                    CASE WHEN games_played > 0
                           THEN ROUND(correct_answers * 100.0 / (correct_answers + wrong_answers))
                           ELSE 0 END as accuracy
               FROM users
               WHERE games_played > 0
               ORDER BY total_score DESC                      LIMIT ?""",
            (limit,),
        ) as cur:                                          rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_user_rank(user_id: int) -> int:      async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(                             """SELECT COUNT(*) + 1 FROM users
               WHERE total_score > (SELECT total_score FROM users WHERE user_id = ?)
               AND games_played > 0""",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
        return row[0] if row else 0

                                               # ─── QUESTIONS ───────────────────────────────────────────────────────────────

async def get_questions(category: str = None, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if category and category != "all":
            async with db.execute(
                """SELECT * FROM questions WHERE approved = 1 AND category = ?
                   ORDER BY RANDOM() LIMIT ?""",
                (category, limit),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                """SELECT * FROM questions WHERE approved = 1
                   ORDER BY RANDOM() LIMIT ?""",
                (limit,),
            ) as cur:                                          rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_categories() -> list[str]:           async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT DISTINCT category, COUNT(*) as cnt
               FROM questions WHERE approved = 1
               GROUP BY category ORDER BY category"""
        ) as cur:
            rows = await cur.fetchall()
        return [(r[0], r[1]) for r in rows]


async def add_question(data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO questions
               (category, question, option_a, option_b, option_c, option_d,
                correct, difficulty, added_by, approved)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["category"], data["question"],
                data["option_a"], data["option_b"],                                                           data["option_c"], data["option_d"],
                data["correct"], data.get("difficulty", "medium"),
                data.get("added_by"), data.get("approved", 0),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def get_question_count(category: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        if category:
            async with db.execute(                             "SELECT COUNT(*) FROM questions WHERE approved=1 AND category=?",
                (category,),
            ) as cur:
                row = await cur.fetchone()
        else:
            async with db.execute(
                "SELECT COUNT(*) FROM questions WHERE approved=1"
            ) as cur:
                row = await cur.fetchone()
        return row[0] if row else 0            

async def delete_question(question_id: int) -> bool:
    """Delete a question by ID. Returns True if deleted, False if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id FROM questions WHERE id=?", (question_id,)
        ) as cur:
            exists = await cur.fetchone()
        if not exists:
            return False
        await db.execute("DELETE FROM questions WHERE id=?", (question_id,))
        await db.commit()
        return True


async def search_questions(keyword: str, limit: int = 20) -> list[dict]:
    """Search questions by keyword in question text or category."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM questions
               WHERE question LIKE ? OR category LIKE ?                                                      ORDER BY id DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", limit),                                                  ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]         

# ─── PENDING QUESTIONS ───────────────────────────────────────────────────────

async def submit_question(user_id: int, data: dict) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO pending_questions
               (submitted_by, category, question, option_a, option_b, option_c, option_d,
                correct, difficulty)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id, data["category"], data["question"],
                data["option_a"], data["option_b"],
                data["option_c"], data["option_d"],
                data["correct"], data.get("difficulty", "medium"),
            ),
        )
        await db.commit()
        return cur.lastrowid


async def get_pending_questions(limit: int = 5) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM pending_questions WHERE status='pending'
               ORDER BY created_at ASC LIMIT ?""",
            (limit,),                                  ) as cur:
            rows = await cur.fetchall()                return [dict(r) for r in rows]         
                                               async def approve_pending(pending_id: int, admin_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM pending_questions WHERE id=?", (pending_id,)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return False
        q = dict(row)
        await add_question({
            "category": q["category"], "question": q["question"],
            "option_a": q["option_a"], "option_b": q["option_b"],
            "option_c": q["option_c"], "option_d": q["option_d"],
            "correct": q["correct"], "difficulty": q["difficulty"],                                       "added_by": q["submitted_by"], "approved": 1,                                             })
        await db.execute(
            "UPDATE pending_questions SET status='approved', reviewed_by=? WHERE id=?",
            (admin_id, pending_id),
        )
        await db.commit()
        return True

                                               async def reject_pending(pending_id: int, admin_id: int):                                         async with aiosqlite.connect(DB_PATH) as db:                                                      await db.execute(                                  "UPDATE pending_questions SET status='rejected', reviewed_by=? WHERE id=?",
            (admin_id, pending_id),
        )
        await db.commit()


# ─── GAME SESSION ─────────────────────────────────────────────────────────────

async def create_session(user_id: int, category: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO game_sessions (user_id, category) VALUES (?, ?)",
            (user_id, category),
        )
        await db.commit()
        return cur.lastrowid

                                               async def finish_session(session_id: int, score: int, correct: int, wrong: int,                                        total: int, streak: int):
    async with aiosqlite.connect(DB_PATH) as db:                                                      await db.execute(
            """UPDATE game_sessions SET                        score=?, correct=?, wrong=?, total_q=?, streak=?, finished_at=?
               WHERE id=?""",
            (score, correct, wrong, total, streak, datetime.now().isoformat(), session_id),
        )
        await db.commit()


# ─── BOT SETTINGS (v1.2) ──────────────────────────────────────────────────────

async def get_bot_settings() -> dict:
    """Get global bot settings."""
    async with aiosqlite.connect(DB_PATH) as db:                                                      db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM bot_settings WHERE id=1") as cur:
            row = await cur.fetchone()                 return dict(row) if row else {
            "default_questions_count": 15,
            "default_time_limit": 30,
            "max_answer_options": 4,
            "max_correct_answers": 1,
            "shuffle_questions": 1,
            "shuffle_answers": 1,                      }

                                               async def update_bot_settings(settings: dict):
    """Update global bot settings."""              async with aiosqlite.connect(DB_PATH) as db:                                                      await db.execute(
            """UPDATE bot_settings SET
                default_questions_count = ?,
                default_time_limit = ?,
                max_answer_options = ?,
                max_correct_answers = ?,
                shuffle_questions = ?,
                shuffle_answers = ?
               WHERE id = 1""",
            (
                settings.get("default_questions_count", 15),
                settings.get("default_time_limit", 30),
                settings.get("max_answer_options", 4),
                settings.get("max_correct_answers", 1),
                settings.get("shuffle_questions", 1),
                settings.get("shuffle_answers", 1),
            ),
        )                                              await db.commit()
                                               
# ─── USER QUIZ SETTINGS ───────────────────────────────────────────────────────
                                               async def get_user_quiz_settings(user_id: int) -> Optional[dict]:
    """Get user's personal quiz settings."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row                 async with db.execute(
            "SELECT * FROM user_quiz_settings WHERE user_id=?", (user_id,)
        ) as cur:                                          row = await cur.fetchone()
        return dict(row) if row else None
                                               
async def update_user_quiz_settings(user_id: int, questions_count: int = None,
                                     time_limit: int = None, shuffle_questions: int = None,
                                     shuffle_answers: int = None):
    """Update user's quiz settings."""             async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO user_quiz_settings
               (user_id, questions_count, time_limit, shuffle_questions, shuffle_answers)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   questions_count = COALESCE(excluded.questions_count, questions_count),
                   time_limit = COALESCE(excluded.time_limit, time_limit),
                   shuffle_questions = COALESCE(excluded.shuffle_questions, shuffle_questions),
                   shuffle_answers = COALESCE(excluded.shuffle_answers, shuffle_answers)""",
            (user_id, questions_count, time_limit, shuffle_questions, shuffle_answers),
        )
        await db.commit()


async def get_effective_quiz_settings(user_id: int) -> dict:
    """Get effective settings (user's or global defaults)."""
    bot_settings = await get_bot_settings()
    user_settings = await get_user_quiz_settings(user_id)                                     
    return {
        "questions_count": (
            user_settings["questions_count"]               if user_settings and user_settings["questions_count"]
            else bot_settings["default_questions_count"]
        ),
        "time_limit": (
            user_settings["time_limit"]
            if user_settings and user_settings["time_limit"] is not None
            else bot_settings["default_time_limit"]
        ),
        "shuffle_questions": (
            user_settings["shuffle_questions"]
            if user_settings and user_settings["shuffle_questions"] is not None
            else bot_settings["shuffle_questions"]
        ),                                             "shuffle_answers": (
            user_settings["shuffle_answers"]
            if user_settings and user_settings["shuffle_answers"] is not None
            else bot_settings["shuffle_answers"]
        ),                                         }
                                               
# ─── VARIANTS ──────────────────────────────────────────────────────────────────

async def get_variants(category: str = None) -> list[dict]:
    """Get all variants, optionally filtered by category."""
    async with aiosqlite.connect(DB_PATH) as db:                                                      db.row_factory = aiosqlite.Row
        if category:
            async with db.execute(
                """SELECT v.*, COUNT(q.id) as questions_count
                   FROM variants v
                   LEFT JOIN questions q ON q.variant_id = v.id
                   WHERE v.category = ?
                   GROUP BY v.id                                  ORDER BY v.variant_number""",
                (category,),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                """SELECT v.*, COUNT(q.id) as questions_count
                   FROM variants v
                   LEFT JOIN questions q ON q.variant_id = v.id
                   GROUP BY v.id
                   ORDER BY v.category, v.variant_number"""
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def add_variant(category: str, variant_number: int, name: str,
                      description: str = "") -> int:
    """Add a new variant."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO variants (category, variant_number, name, description)
               VALUES (?, ?, ?, ?)""",
            (category, variant_number, name, description),
        )
        await db.commit()
        return cur.lastrowid


async def update_variant(variant_id: int, name: str = None,
                        description: str = None) -> bool:
    """Update variant details."""
    async with aiosqlite.connect(DB_PATH) as db:
        if name and description is not None:
            await db.execute(
                "UPDATE variants SET name=?, description=? WHERE id=?",
                (name, description, variant_id),
            )
        elif name:
            await db.execute(
                "UPDATE variants SET name=? WHERE id=?",
                (name, variant_id),
            )
        elif description is not None:
            await db.execute(
                "UPDATE variants SET description=? WHERE id=?",
                (description, variant_id),
            )
        await db.commit()
        return True


async def delete_variant(variant_id: int) -> bool:
    """Delete a variant and unlink its questions."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if exists
        async with db.execute(
            "SELECT id FROM variants WHERE id=?", (variant_id,)
        ) as cur:
            exists = await cur.fetchone()
        if not exists:
            return False

        # Unlink questions (set variant_id to NULL)
        await db.execute(
            "UPDATE questions SET variant_id=NULL WHERE variant_id=?",
            (variant_id,),
        )

        # Delete variant
        await db.execute("DELETE FROM variants WHERE id=?", (variant_id,))
        await db.commit()
        return True

                                               async def get_variant_by_id(variant_id: int) -> Optional[dict]:
    """Get variant by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM variants WHERE id=?", (variant_id,)
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None

                                               # ─── CATEGORY MANAGEMENT ──────────────────────────────────────────────────────

async def rename_category(old_name: str, new_name: str) -> bool:
    """Rename a category (updates questions and variants)."""
    async with aiosqlite.connect(DB_PATH) as db:                                                      await db.execute(
            "UPDATE questions SET category=? WHERE category=?",
            (new_name, old_name),
        )
        await db.execute(
            "UPDATE variants SET category=? WHERE category=?",
            (new_name, old_name),
        )
        await db.commit()
        return True


async def delete_category(category: str) -> int:                                                  """Delete category and all its questions/variants. Returns deleted count."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Count questions
        async with db.execute(
            "SELECT COUNT(*) FROM questions WHERE category=?", (category,)
        ) as cur:                                          q_count = (await cur.fetchone())[0]

        # Delete questions                             await db.execute("DELETE FROM questions WHERE category=?", (category,))

        # Delete variants
        await db.execute("DELETE FROM variants WHERE category=?", (category,))

        await db.commit()
        return q_count


# ─── ҰБТ РЕЖИМІ (v1.4) ─────────────────────────────────────────────────────────

async def get_ubt_subjects(is_mandatory: int = None) -> list[dict]:
    """Get all UBT subjects, optionally filtered by mandatory status."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if is_mandatory is not None:
            async with db.execute(
                """SELECT * FROM ubt_subjects
                   WHERE is_mandatory = ?
                   ORDER BY name""",
                (is_mandatory,)
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                """SELECT * FROM ubt_subjects
                   ORDER BY is_mandatory DESC, name"""
            ) as cur:
                rows = await cur.fetchall()
                                                       return [dict(r) for r in rows]
                                               
async def add_ubt_subject(name: str, is_mandatory: int = 0,
                          questions_count: int = 25, time_minutes: int = 45) -> int:
    """Add UBT subject."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO ubt_subjects (name, is_mandatory, questions_count, time_minutes)
               VALUES (?, ?, ?, ?)""",
            (name, is_mandatory, questions_count, time_minutes),
        )
        await db.commit()
        return cur.lastrowid


async def get_ubt_topics(subject_id: int = None) -> list[dict]:
    """Get UBT topics, optionally filtered by subject."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if subject_id:
            async with db.execute(
                """SELECT t.*, s.name as subject_name,                                                           COUNT(q.id) as questions_count
                   FROM ubt_topics t
                   JOIN ubt_subjects s ON s.id = t.subject_id
                   LEFT JOIN questions q ON q.ubt_topic_id = t.id
                   WHERE t.subject_id = ?
                   GROUP BY t.id
                   ORDER BY t.name""",                         (subject_id,),
            ) as cur:
                rows = await cur.fetchall()
        else:
            async with db.execute(
                """SELECT t.*, s.name as subject_name,
                   COUNT(q.id) as questions_count
                   FROM ubt_topics t
                   JOIN ubt_subjects s ON s.id = t.subject_id
                   LEFT JOIN questions q ON q.ubt_topic_id = t.id
                   GROUP BY t.id
                   ORDER BY s.name, t.name"""
            ) as cur:
                rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def add_ubt_topic(subject_id: int, name: str) -> int:
    """Add UBT topic to subject."""
    async with aiosqlite.connect(DB_PATH) as db:                                                      cur = await db.execute(
            "INSERT INTO ubt_topics (subject_id, name) VALUES (?, ?)",
            (subject_id, name),
        )
        await db.commit()                              return cur.lastrowid


async def save_ubt_result(session_id: int, subject_id: int,
                         score: int, correct: int, wrong: int, skipped: int):
    """Save UBT result for a subject."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO ubt_results (session_id, subject_id, score, correct, wrong, skipped)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, subject_id, score, correct, wrong, skipped),                                 )
        await db.commit()


async def finish_ubt_session(session_id: int, total_score: int):
    """Finish UBT session."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE ubt_sessions SET total_score=?, finished_at=?
               WHERE id=?""",
            (total_score, datetime.now().isoformat(), session_id),
        )
        await db.commit()


async def get_ubt_questions(topic_id: int, limit: int = 25) -> list[dict]:                        """Get questions for UBT topic."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM questions                        WHERE ubt_topic_id = ? AND approved = 1
               ORDER BY RANDOM() LIMIT ?""",
            (topic_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_user_ubt_history(user_id: int, limit: int = 10) -> list[dict]:
    """Get user's UBT session history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(                             """SELECT * FROM ubt_sessions
               WHERE user_id = ? AND finished_at IS NOT NULL
               ORDER BY finished_at DESC LIMIT ?""",
            (user_id, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ═══ UBT ADDITIONAL FUNCTIONS ═══

async def get_ubt_subject_by_id(subject_id: int) -> Optional[dict]:
    """Get UBT subject by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ubt_subjects WHERE id=?", (subject_id,)
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None


async def get_ubt_subject_by_name(name: str) -> Optional[dict]:
    """Get UBT subject by name."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ubt_subjects WHERE name=?", (name,)
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None


async def create_ubt_session(user_id: int, session_type: str,
                            elective1_id: int, elective2_id: int) -> int:
    """Create new UBT session."""
    async with aiosqlite.connect(DB_PATH) as db:                                                      cur = await db.execute(
            """INSERT INTO ubt_sessions
               (user_id, mode, session_type, elective1_id, elective2_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, session_type, session_type, elective1_id, elective2_id),
        )
        await db.commit()
        return cur.lastrowid


async def finish_ubt_session(session_id: int, mandatory_score: int,
                            elective1_score: int, elective2_score: int,
                            total_score: int, total_correct: int,
                            total_wrong: int):
    """Finish UBT session with scores."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE ubt_sessions SET
                mandatory_score=?, elective1_score=?, elective2_score=?,
                total_score=?, total_correct=?, total_wrong=?,
                finished_at=?
               WHERE id=?""",
            (mandatory_score, elective1_score, elective2_score,
             total_score, total_correct, total_wrong,
             datetime.now().isoformat(), session_id),
        )
        await db.commit()


# ═══ BROADCAST FUNCTIONS ═══

async def get_all_user_ids() -> list[int]:
    """Get all user IDs."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
        return [row[0] for row in rows]


async def get_active_user_ids(days: int = 7) -> list[int]:
    """Get users active in last N days."""
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT DISTINCT user_id FROM game_sessions
               WHERE started_at > ?""",
            (cutoff,)                                  ) as cur:
            rows = await cur.fetchall()
        return [row[0] for row in rows]        

async def create_broadcast(admin_id: int, message_text: str,
                          message_type: str = 'text', media_url: str = None,
                          target_type: str = 'all', total_users: int = 0) -> int:
    """Create new broadcast."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO broadcasts
               (admin_id, message_text, message_type, media_url, target_type, total_users)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (admin_id, message_text, message_type, media_url, target_type, total_users),              )
        await db.commit()
        return cur.lastrowid                   
                                               async def update_broadcast_stats(broadcast_id: int, sent: int, failed: int):
    """Update broadcast statistics."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE broadcasts SET
                sent_count = ?, failed_count = ?, finished_at = ?
               WHERE id = ?""",
            (sent, failed, datetime.now().isoformat(), broadcast_id),
        )
        await db.commit()


async def get_broadcast_history(admin_id: int = None, limit: int = 10) -> list[dict]:
    """Get broadcast history."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if admin_id:
            async with db.execute(
                """SELECT * FROM broadcasts
                   WHERE admin_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (admin_id, limit),
            ) as cur:
                rows = await cur.fetchall()
        else:                                              async with db.execute(
                """SELECT * FROM broadcasts
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            ) as cur:
                rows = await cur.fetchall()

        return [dict(r) for r in rows]


async def add_ubt_subject(name: str, is_mandatory: int = 0,                                                            questions_count: int = 20, time_minutes: int = 30) -> int:
    """Add new UBT subject."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get max display_order
        async with db.execute(
            "SELECT COALESCE(MAX(id), 0) FROM ubt_subjects"
        ) as cur:
            max_id = (await cur.fetchone())[0]

        cur = await db.execute(
            """INSERT INTO ubt_subjects (name, is_mandatory)
               VALUES (?, ?)""",
            (name, is_mandatory),
        )                                              await db.commit()
        return cur.lastrowid


async def delete_ubt_subject(subject_id: int) -> bool:
    """Delete UBT subject."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if exists
        async with db.execute(
            "SELECT id, is_mandatory FROM ubt_subjects WHERE id=?", (subject_id,)                     ) as cur:
            row = await cur.fetchone()

        if not row:
            return False

        # Don't delete mandatory subjects
        if row[1]:
            return False

        # Delete subject                               await db.execute("DELETE FROM ubt_subjects WHERE id=?", (subject_id,))
        await db.commit()                              return True


async def get_ubt_questions_by_type(subject_id: int, question_type: str, limit: int) -> list[dict]:
    """Get UBT questions by subject and type."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM questions
               WHERE category = (SELECT name FROM ubt_subjects WHERE id = ?)
               AND question_type = ?
               AND approved = 1
               ORDER BY RANDOM() LIMIT ?""",
            (subject_id, question_type, limit),
        ) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ═══ ҰБТ QUESTIONS FUNCTIONS (v2.0) ═══════════════════════════════════════                  
async def add_ubt_question(subject_id: int, question_type: str, question_text: str,
                          **kwargs) -> int:
    """Add ҰБТ question (separate from quiz questions)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Build query based on question type
        if question_type == 'simple' or question_type == 'context':
            cur = await db.execute(
                """INSERT INTO ubt_questions
                   (subject_id, question_type, question_text, context_text,
                    option_a, option_b, option_c, option_d, correct,
                    image_url, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (subject_id, question_type, question_text,
                 kwargs.get('context_text'),
                 kwargs.get('option_a'), kwargs.get('option_b'),
                 kwargs.get('option_c'), kwargs.get('option_d'),
                 kwargs.get('correct'),
                 kwargs.get('image_url'), kwargs.get('difficulty', 'medium'))
            )
        elif question_type == 'matching':
            import json
            cur = await db.execute(
                """INSERT INTO ubt_questions
                   (subject_id, question_type, question_text,
                    matching_left, matching_right, matching_answer,
                    image_url, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (subject_id, question_type, question_text,
                 json.dumps(kwargs.get('matching_left')),
                 json.dumps(kwargs.get('matching_right')),                                                     json.dumps(kwargs.get('matching_answer')),
                 kwargs.get('image_url'), kwargs.get('difficulty', 'medium'))
            )
        elif question_type == 'multiple':
            cur = await db.execute(
                """INSERT INTO ubt_questions
                   (subject_id, question_type, question_text,
                    option_a, option_b, option_c, option_d, correct_multiple,
                    image_url, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (subject_id, question_type, question_text,
                 kwargs.get('option_a'), kwargs.get('option_b'),
                 kwargs.get('option_c'), kwargs.get('option_d'),
                 kwargs.get('correct_multiple'),
                 kwargs.get('image_url'), kwargs.get('difficulty', 'medium'))
            )

        await db.commit()
        return cur.lastrowid                   

async def get_ubt_questions_by_subject(subject_id: int, question_type: str = None,
                                       limit: int = None) -> list[dict]:
    """Get ҰБТ questions for a subject."""         async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if question_type:
            query = """SELECT * FROM ubt_questions
                      WHERE subject_id = ? AND question_type = ?
                      ORDER BY RANDOM()"""
            params = (subject_id, question_type)
        else:
            query = """SELECT * FROM ubt_questions
                      WHERE subject_id = ?
                      ORDER BY RANDOM()"""
            params = (subject_id,)

        if limit:
            query += " LIMIT ?"
            params = params + (limit,)

        async with db.execute(query, params) as cur:
            rows = await cur.fetchall()

        return [dict(r) for r in rows]


async def count_ubt_questions(subject_id: int, question_type: str = None) -> int:
    """Count ҰБТ questions."""
    async with aiosqlite.connect(DB_PATH) as db:
        if question_type:
            async with db.execute(
                "SELECT COUNT(*) FROM ubt_questions WHERE subject_id=? AND question_type=?",
                (subject_id, question_type)
            ) as cur:
                row = await cur.fetchone()
        else:
            async with db.execute(
                "SELECT COUNT(*) FROM ubt_questions WHERE subject_id=?",
                (subject_id,)
            ) as cur:
                row = await cur.fetchone()

        return row[0] if row else 0


async def delete_ubt_question(question_id: int):
    """Delete ҰБТ question."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM ubt_questions WHERE id=?", (question_id,))
        await db.commit()
                                               
async def get_ubt_question_by_id(question_id: int) -> Optional[dict]:                             """Get single ҰБТ question."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM ubt_questions WHERE id=?", (question_id,)
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None
                                               
async def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user info by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(                             "SELECT * FROM users WHERE user_id=?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None
