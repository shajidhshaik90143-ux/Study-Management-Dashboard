import sqlite3
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "study.db"

class Database:
    def __init__(self, path=DB_PATH):
        self.path = str(path)

    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        return c

    def execute(self, sql, params=()):
        with self.conn() as c:
            c.execute(sql, params)
            c.commit()

    def query(self, sql, params=()):
        with self.conn() as c:
            return pd.read_sql_query(sql, c, params=params)

    def scalar(self, sql, params=()):
        with self.conn() as c:
            row=c.execute(sql,params).fetchone()
            return row[0] if row else 0

    def get_settings(self):
        df=self.query("SELECT key,value FROM settings")
        return dict(zip(df["key"],df["value"])) if not df.empty else {}

    def set_setting(self,key,value):
        self.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",(key,value))

    def reset(self):
        with self.conn() as c:
            for table in ["study_sessions","attendance","tasks","exams","notes","goals","subjects"]:
                c.execute(f"DELETE FROM {table}")
            c.execute("DELETE FROM settings")
            c.commit()
        seed_settings(self)

db=Database()

def init_db():
    with db.conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS subjects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            teacher TEXT,
            credits INTEGER DEFAULT 3,
            target_score REAL DEFAULT 75,
            color TEXT DEFAULT '#4F7CFF'
        );
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            subject_id INTEGER,
            due_date TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            completed_at TEXT,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            class_date TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(subject_id,class_date),
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS exams(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject_id INTEGER,
            exam_date TEXT NOT NULL,
            exam_type TEXT DEFAULT 'Internal',
            max_marks REAL DEFAULT 100,
            score REAL,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS notes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject_id INTEGER,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS goals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            deadline TEXT,
            progress REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS study_sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            study_date TEXT NOT NULL,
            hours REAL NOT NULL,
            topic TEXT,
            FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
    if not db.get_settings():
        seed_settings(db)

def seed_settings(database):
    defaults={
        "student_name":"Student",
        "semester":"B.Tech 3rd Year",
        "college":"",
        "target_score":"75"
    }
    for k,v in defaults.items():
        database.set_setting(k,v)

init_db()
