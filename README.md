# 🎓 Study Management Dashboard

A strong, local-first student productivity dashboard built with **Python, Streamlit, SQLite and Pandas**.

## Features

- 📊 Dashboard with KPIs and study activity
- 📚 Subject management with targets, credits and teachers
- ✅ Assignment/task manager with priority, deadlines and status
- 📅 Subject-wise attendance tracking
- 📝 Exam and assessment tracker
- 📒 Notes / knowledge vault
- 🎯 Goal and milestone tracker
- ⏱️ Study-session logging
- 📈 Analytics for study hours, performance and task completion
- ⚙️ Student profile/settings
- 💾 SQLite local database — no API keys or cloud setup required
- 🔄 Automatic database initialization
- 🛡️ Reset-data confirmation
- 📱 Responsive Streamlit interface

## Tech stack

Python 3.10–3.13 recommended, Streamlit, Pandas, SQLite.

## Windows setup

```powershell
cd "Study Management Dashboard"
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL shown by Streamlit, normally:
`http://localhost:8501`

## Project structure

```text
Study Management Dashboard/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── study.db              # generated automatically
├── src/
│   ├── __init__.py
│   ├── database.py
│   └── analytics.py
└── .streamlit/
    └── config.toml
```

## First use

1. Open **Settings** and enter your student/college information.
2. Add subjects.
3. Add assignments/tasks.
4. Record attendance.
5. Add upcoming exams.
6. Add notes and goals.
7. Log study sessions in **Analytics**.
8. Return to **Dashboard** to view your overall study status.

## Database

The SQLite file is generated automatically at `data/study.db`. It is intentionally excluded from the ZIP's initial state so the project starts clean.

## Troubleshooting

### `streamlit is not recognized`
Activate the virtual environment and use:

```powershell
python -m streamlit run app.py
```

### Port is busy

```powershell
python -m streamlit run app.py --server.port 8502
```

### Reinstall dependencies

```powershell
python -m pip install -r requirements.txt --upgrade
```
