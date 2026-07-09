# StudyGenie AI — AI-Powered Study Planner & Organizer

StudyGenie AI is a Streamlit study-planning app. It stores data in a local
SQLite database (via SQLAlchemy), renders interactive charts with Plotly, and
uses the Google Gemini API for its optional AI features (summaries, flashcards,
MCQs, timetable generation, chat assistant, and analytics reports).

## 🚀 Features
- **Dashboard** — study streak, pending tasks, upcoming exams, total time studied, today's timetable, and a Pomodoro focus toggle.
- **Subjects** — track subjects with a color tag and logged study hours.
- **Study Planner** — AI-generated weekly timetable plus a manual timetable ledger.
- **Homework Manager** — create, complete, and archive assignments by subject/priority.
- **Exams** — schedule exams with target marks and live countdowns.
- **Notes** — paste raw notes and auto-generate a summary, flashcards, and MCQs.
- **AI Study Assistant** — chat with a study-focused assistant.
- **Analytics** — Plotly charts of study time plus an AI performance report.
- **Goals** — track progress toward numeric objectives.
- **Settings** — edit profile and download a database backup.

> The AI features degrade gracefully: without a Gemini API key they display a
> clear "key missing" notice instead of crashing. Everything else works offline.

---

## 🛠️ Installation

### 1. Project structure
```text
app/
├── app.py            # Streamlit UI + routing
├── database.py       # SQLAlchemy models + seed data
├── ai.py             # Gemini API wrapper (AIService)
├── requirements.txt
├── api.env           # holds GEMINI_API_KEY
└── database/
    └── studygenie.db # created/seeded automatically
```

### 2. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Configure the API key (optional, for AI features)
Edit `api.env` and set your key:
```text
GEMINI_API_KEY=your_real_key_here
```
Get a key from https://aistudio.google.com/app/apikey. The app also reads a
standard `.env` file if present.

### 4. Run
```bash
streamlit run app.py
```
The database is created and seeded with sample data on first launch.

## 🧩 Tech stack
Python 3.13 · Streamlit · SQLAlchemy · SQLite · Pandas · Plotly · Google Gemini
