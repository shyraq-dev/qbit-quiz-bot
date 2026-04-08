# ⚡ QBit Quiz Bot

> Білімді битке бөліп, жеңіске жинайтын қазақша Telegram боты.

---

## 📁 Файл құрылымы

```
qbit_quiz_bot/
├── bot.py               # Негізгі іске қосу файлы
├── config.py            # Конфигурация
├── database.py          # SQLite дерекқор логикасы
├── keyboards.py         # Барлық батырмалар
├── seed_questions.py    # Үлгі сұрақтар қосу
├── requirements.txt     # Python тәуелділіктері
├── .env.example         # Конфигурация үлгісі
└── handlers/
    ├── start_handler.py       # /start, туралы
    ├── quiz_handler.py        # Тест логикасы
    ├── stats_handler.py       # Статистика
    ├── leaderboard_handler.py # Рейтинг
    └── admin_handler.py       # Админ панелі
```

---

## 🚀 Іске қосу

### 1. Орнату

```bash
# Жоба директориясына кір
cd qbit_quiz_bot

# Virtual environment жасау (ұсынылады)
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# Тәуелділіктерді орнату
pip install -r requirements.txt
```

### 2. Конфигурация

```bash
# .env файлын жасау
cp .env.example .env

# .env файлын өңдеу:
# BOT_TOKEN — BotFather-дан алынған токен
# ADMIN_IDS — Telegram user_id (adminдер)
```

### 3. Деректер базасын баптау

```bash
# Үлгі сұрақтарды қосу (алғашқы іске қосу үшін)
python seed_questions.py
```

### 4. Іске қосу

```bash
python bot.py
```

---

## ⚙️ Мүмкіндіктер

| Мүмкіндік | Сипаттама |
|-----------|-----------|
| 🎯 Тест | Категория бойынша 10 сұрақ |
| 🔥 Streak | 3 қатар дұрыс = бонус ұпай |
| 📊 Статистика | Дәлдік, streak, ұпай, рейтинг |
| 🏆 Leaderboard | ТОП-10 ойыншылар |
| 💡 Сұрақ жіберу | Қолданушылар сұрақ ұсына алады |
| 🛠 Админ панелі | Сұрақтарды бекіту/қабылдамау |

---

## 👤 Пайдалану

### Қолданушылар үшін:
- `/start` — Ботты бастау
- **🎯 Тест бастау** — Категория таңдап, тест тапсыру
- **📊 Статистика** — Жеке нәтижелер
- **🏆 Рейтинг** — ТОП ойыншылар
- **💡 Сұрақ жіберу** — Сұрақ ұсыну

### Админдер үшін:
- `/admin` — Админ панеліне кіру
- **📋 Кезектегі сұрақтар** — Ұсынылған сұрақтарды тексеру
- **➕ Сұрақ қосу** — Тікелей сұрақ қосу
- **📊 Бот статистикасы** — Жалпы аналитика

---

## 🗄️ Деректер базасы

SQLite (qbit_quiz.db) автоматты жасалады.

**Кестелер:**
- `users` — Ойыншылар профилі мен статистикасы
- `questions` — Сұрақтар базасы
- `game_sessions` — Ойын сеанстары
- `pending_questions` — Тексерілетін сұрақтар

---

## 🏗️ Деплой (Linux VPS)

```bash
# systemd service жасау
sudo nano /etc/systemd/system/qbit-quiz.service
```

```ini
[Unit]
Description=QBit Quiz Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/qbit_quiz_bot
ExecStart=/home/ubuntu/qbit_quiz_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable qbit-quiz
sudo systemctl start qbit-quiz
sudo systemctl status qbit-quiz
```
