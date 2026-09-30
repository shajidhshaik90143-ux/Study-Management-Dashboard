from datetime import date, timedelta
import pandas as pd
from .database import db

def get_dashboard_metrics():
    study_hours=float(db.scalar("SELECT COALESCE(SUM(hours),0) FROM study_sessions"))
    week_start=date.today()-timedelta(days=6)
    week_hours=float(db.scalar("SELECT COALESCE(SUM(hours),0) FROM study_sessions WHERE study_date>=?",(week_start.isoformat(),)))
    pending=int(db.scalar("SELECT COUNT(*) FROM tasks WHERE status='Pending'"))
    completed=int(db.scalar("SELECT COUNT(*) FROM tasks WHERE status='Completed'"))
    subjects=int(db.scalar("SELECT COUNT(*) FROM subjects"))
    exams=int(db.scalar("SELECT COUNT(*) FROM exams WHERE exam_date BETWEEN ? AND ?",(date.today().isoformat(),(date.today()+timedelta(days=30)).isoformat())))
    total=int(db.scalar("SELECT COUNT(*) FROM attendance"))
    present=int(db.scalar("SELECT COUNT(*) FROM attendance WHERE status='Present'"))
    attendance=(present/total*100) if total else 0
    return dict(study_hours=study_hours,week_hours=week_hours,pending_tasks=pending,
                completed_tasks=completed,subjects=subjects,exams_soon=exams,attendance=attendance)

def get_subject_performance():
    q="""SELECT s.name subject,
                ROUND(AVG(CASE WHEN e.max_marks>0 THEN e.score*100.0/e.max_marks END),1) score
         FROM subjects s LEFT JOIN exams e ON e.subject_id=s.id
         GROUP BY s.id,s.name HAVING score IS NOT NULL ORDER BY score DESC"""
    return db.query(q)

def get_weekly_study():
    start=date.today()-timedelta(days=6)
    df=db.query("""SELECT study_date day, SUM(hours) hours FROM study_sessions
                   WHERE study_date>=? GROUP BY study_date ORDER BY study_date""",(start.isoformat(),))
    if df.empty: return df
    full=pd.DataFrame({"day":[(start+timedelta(days=i)).isoformat() for i in range(7)]})
    return full.merge(df,on="day",how="left").fillna({"hours":0})

def get_task_summary():
    return db.query("""SELECT status, COUNT(*) tasks FROM tasks GROUP BY status ORDER BY status""")

def get_attendance_summary():
    return db.query("""SELECT s.name subject,
                              COUNT(a.id) total_classes,
                              SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) present,
                              ROUND(SUM(CASE WHEN a.status='Present' THEN 1.0 ELSE 0 END)*100/COUNT(a.id),1) attendance
                       FROM subjects s JOIN attendance a ON a.subject_id=s.id
                       GROUP BY s.id,s.name ORDER BY attendance DESC""")

def get_upcoming_exams(days=30):
    end=date.today()+timedelta(days=days)
    return db.query("""SELECT e.title,COALESCE(s.name,'General') subject,e.exam_date,
                              e.exam_type,e.max_marks,e.score
                       FROM exams e LEFT JOIN subjects s ON s.id=e.subject_id
                       WHERE e.exam_date BETWEEN ? AND ?
                       ORDER BY e.exam_date""",(date.today().isoformat(),end.isoformat()))
