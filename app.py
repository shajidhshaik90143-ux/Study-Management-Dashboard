import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from src.database import init_db, db
from src.analytics import (
    get_dashboard_metrics, get_subject_performance, get_weekly_study,
    get_task_summary, get_attendance_summary, get_upcoming_exams
)

st.set_page_config(
    page_title="Study Management Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ---------- Theme ----------
st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(128,128,128,.18);
    padding: 14px 16px;
    border-radius: 14px;
}
.hero {
    padding: 1.4rem 1.6rem;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,.18);
    background: linear-gradient(135deg, rgba(70,100,180,.18), rgba(120,70,170,.12));
    margin-bottom: 1rem;
}
.small-muted {color:#8b95a7;font-size:.9rem;}
.card {
    border:1px solid rgba(128,128,128,.18);
    border-radius:14px;
    padding:15px;
    margin-bottom:10px;
}
.priority-high {border-left:4px solid #ef4444;}
.priority-medium {border-left:4px solid #f59e0b;}
.priority-low {border-left:4px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.title("🎓 StudyHub")
    st.caption("Study Management Dashboard")
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📚 Subjects", "✅ Tasks", "📅 Attendance",
         "📝 Exams", "📒 Notes", "🎯 Goals", "📊 Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    st.divider()
    profile = db.get_settings()
    st.write(f"**Student:** {profile.get('student_name','Student')}")
    st.write(f"**Semester:** {profile.get('semester','Not set')}")
    st.caption("Local-first • SQLite • No cloud required")

# ---------- Dashboard ----------
if page == "🏠 Dashboard":
    metrics = get_dashboard_metrics()
    st.markdown(f"""
    <div class="hero">
      <h1 style="margin:0">Good day, {profile.get('student_name','Student')} 👋</h1>
      <p class="small-muted">Your study command center — track learning, deadlines, attendance and progress.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(5)
    cols[0].metric("Study Hours", f"{metrics['study_hours']:.1f} h", f"{metrics['week_hours']:.1f} h this week")
    cols[1].metric("Tasks", metrics["pending_tasks"], f"{metrics['completed_tasks']} completed")
    cols[2].metric("Attendance", f"{metrics['attendance']:.1f}%", "overall")
    cols[3].metric("Subjects", metrics["subjects"], "active")
    cols[4].metric("Exams Soon", metrics["exams_soon"], "next 30 days")

    st.subheader("📈 Study activity")
    c1, c2 = st.columns(2)
    with c1:
        weekly = get_weekly_study()
        if not weekly.empty:
            st.bar_chart(weekly.set_index("day")["hours"], height=280)
        else:
            st.info("No study sessions yet. Add sessions from Analytics.")
    with c2:
        perf = get_subject_performance()
        if not perf.empty:
            st.bar_chart(perf.set_index("subject")["score"], height=280)
        else:
            st.info("Add subjects and marks to see performance.")

    st.subheader("⏰ Upcoming exams")
    exams = get_upcoming_exams(30)
    if exams.empty:
        st.success("No exams scheduled in the next 30 days.")
    else:
        st.dataframe(exams, use_container_width=True, hide_index=True)

    st.subheader("🧭 Quick actions")
    q = st.columns(4)
    if q[0].button("➕ Add task", use_container_width=True): st.session_state["jump"] = "tasks"
    if q[1].button("📚 Add subject", use_container_width=True): st.session_state["jump"] = "subjects"
    if q[2].button("⏱️ Log study", use_container_width=True): st.session_state["jump"] = "analytics"
    if q[3].button("📝 Add exam", use_container_width=True): st.session_state["jump"] = "exams"

# ---------- Subjects ----------
elif page == "📚 Subjects":
    st.title("📚 Subjects")
    tab1, tab2 = st.tabs(["Subject list", "Add subject"])
    with tab1:
        subjects = db.query("SELECT * FROM subjects ORDER BY name")
        if subjects.empty:
            st.info("No subjects yet. Add your first subject.")
        else:
            for _, r in subjects.iterrows():
                with st.container(border=True):
                    a,b,c,d = st.columns([3,1.5,1.5,1])
                    a.markdown(f"**{r['name']}**  \n{r['code'] or 'No code'}")
                    b.metric("Target", f"{r['target_score']:.0f}%")
                    b.caption(r["teacher"] or "Teacher not set")
                    c.metric("Credits", int(r["credits"]))
                    c.caption(f"Color: {r['color']}")
                    if d.button("🗑️", key=f"del_sub_{r['id']}"):
                        db.execute("DELETE FROM subjects WHERE id=?", (int(r["id"]),))
                        st.rerun()
    with tab2:
        with st.form("subject_form"):
            name = st.text_input("Subject name *")
            code = st.text_input("Subject code")
            teacher = st.text_input("Teacher")
            credits = st.number_input("Credits", 1, 10, 3)
            target = st.number_input("Target score (%)", 0.0, 100.0, 75.0)
            color = st.color_picker("Subject color", "#4F7CFF")
            submitted = st.form_submit_button("Add subject", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Subject name is required.")
                else:
                    db.execute("""INSERT INTO subjects(name,code,teacher,credits,target_score,color)
                                  VALUES(?,?,?,?,?,?)""",
                               (name.strip(), code.strip(), teacher.strip(), credits, target, color))
                    st.success("Subject added.")
                    st.rerun()

# ---------- Tasks ----------
elif page == "✅ Tasks":
    st.title("✅ Task & Assignment Manager")
    c1,c2,c3 = st.columns(3)
    status_filter = c1.selectbox("Status", ["All","Pending","Completed"])
    priority_filter = c2.selectbox("Priority", ["All","High","Medium","Low"])
    search = c3.text_input("Search", placeholder="assignment, lab, project...")
    query = """SELECT t.id,t.title,t.description,t.due_date,t.priority,t.status,
                      COALESCE(s.name,'General') subject
               FROM tasks t LEFT JOIN subjects s ON s.id=t.subject_id
               WHERE 1=1"""
    params=[]
    if status_filter != "All": query += " AND t.status=?"; params.append(status_filter)
    if priority_filter != "All": query += " AND t.priority=?"; params.append(priority_filter)
    if search.strip(): query += " AND (t.title LIKE ? OR t.description LIKE ?)"; params += [f"%{search}%",f"%{search}%"]
    query += " ORDER BY CASE t.status WHEN 'Pending' THEN 0 ELSE 1 END, t.due_date"
    tasks = db.query(query, tuple(params))
    if not tasks.empty:
        for _, r in tasks.iterrows():
            due = pd.to_datetime(r["due_date"]).date() if pd.notna(r["due_date"]) else None
            overdue = due and due < date.today() and r["status"] == "Pending"
            with st.container(border=True):
                a,b,c,d = st.columns([4,2,1.5,1])
                icon = "🔴" if r["priority"]=="High" else ("🟠" if r["priority"]=="Medium" else "🟢")
                a.markdown(f"**{icon} {r['title']}**  \n{r['subject']} • {r['description'] or ''}")
                b.write(f"Due: **{due or 'No date'}**")
                if overdue: b.error("Overdue")
                else: b.write("")
                if c.button("✓ Complete" if r["status"]=="Pending" else "↩ Pending", key=f"task_{r['id']}"):
                    new = "Completed" if r["status"]=="Pending" else "Pending"
                    db.execute("UPDATE tasks SET status=?, completed_at=? WHERE id=?",
                               (new, datetime.now().isoformat() if new=="Completed" else None, int(r["id"])))
                    st.rerun()
                if d.button("🗑️", key=f"taskdel_{r['id']}"):
                    db.execute("DELETE FROM tasks WHERE id=?", (int(r["id"]),)); st.rerun()
    else:
        st.info("No tasks match your filters.")

    st.divider()
    st.subheader("➕ Add task")
    subjects = db.query("SELECT id,name FROM subjects ORDER BY name")
    options = {"General": None} | {r["name"]: int(r["id"]) for _,r in subjects.iterrows()}
    with st.form("task_form"):
        a,b = st.columns(2)
        title = a.text_input("Task title *")
        subject = b.selectbox("Subject", list(options.keys()))
        description = st.text_area("Description")
        a,b,c = st.columns(3)
        due = a.date_input("Due date", date.today())
        priority = b.selectbox("Priority", ["High","Medium","Low"], index=1)
        status = c.selectbox("Status", ["Pending","Completed"])
        if st.form_submit_button("Add task", type="primary"):
            if title.strip():
                db.execute("""INSERT INTO tasks(title,description,subject_id,due_date,priority,status,completed_at)
                              VALUES(?,?,?,?,?,?,?)""",
                           (title.strip(),description.strip(),options[subject],due.isoformat(),priority,status,
                            datetime.now().isoformat() if status=="Completed" else None))
                st.success("Task added."); st.rerun()
            else: st.error("Task title is required.")

# ---------- Attendance ----------
elif page == "📅 Attendance":
    st.title("📅 Attendance Tracker")
    summary = get_attendance_summary()
    if not summary.empty:
        st.dataframe(summary, use_container_width=True, hide_index=True)
        st.caption("Attendance below 75% is highlighted by the dashboard metrics.")
    else:
        st.info("No attendance records yet.")

    subjects = db.query("SELECT id,name FROM subjects ORDER BY name")
    if subjects.empty:
        st.warning("Add subjects first.")
    else:
        with st.form("attendance_form"):
            s = st.selectbox("Subject", subjects["name"].tolist())
            idx = subjects.index[subjects["name"] == s][0]
            sid = int(subjects.loc[idx,"id"])
            att_date = st.date_input("Class date", date.today())
            status = st.radio("Class status", ["Present","Absent"], horizontal=True)
            if st.form_submit_button("Record attendance", type="primary"):
                db.execute("""INSERT OR REPLACE INTO attendance(subject_id,class_date,status)
                              VALUES(?,?,?)""", (sid,att_date.isoformat(),status))
                st.success("Attendance recorded."); st.rerun()

# ---------- Exams ----------
elif page == "📝 Exams":
    st.title("📝 Exams & Assessments")
    exams = db.query("""SELECT e.id,e.title,e.exam_date,e.exam_type,e.max_marks,e.score,
                               COALESCE(s.name,'General') subject
                        FROM exams e LEFT JOIN subjects s ON s.id=e.subject_id
                        ORDER BY e.exam_date""")
    if not exams.empty:
        display = exams.copy()
        display["exam_date"] = pd.to_datetime(display["exam_date"]).dt.date
        st.dataframe(display, use_container_width=True, hide_index=True)
        for _,r in exams.iterrows():
            with st.container(border=True):
                a,b,c = st.columns([4,2,1])
                a.write(f"**{r['title']}** — {r['subject']} ({r['exam_type']})")
                b.write(f"{r['exam_date']} • {r['score'] if pd.notna(r['score']) else 'Not graded'}/{r['max_marks']}")
                if c.button("🗑️", key=f"exam_{r['id']}"):
                    db.execute("DELETE FROM exams WHERE id=?", (int(r["id"]),)); st.rerun()
    else: st.info("No exams added.")

    subjects = db.query("SELECT id,name FROM subjects ORDER BY name")
    options = {"General":None} | {r["name"]:int(r["id"]) for _,r in subjects.iterrows()}
    with st.form("exam_form"):
        a,b = st.columns(2)
        title=a.text_input("Exam title *")
        subject=b.selectbox("Subject", list(options))
        a,b,c=st.columns(3)
        exam_date=a.date_input("Exam date", date.today())
        exam_type=b.selectbox("Type",["Internal","Midterm","End Semester","Quiz","Lab","Viva","Other"])
        max_marks=c.number_input("Maximum marks",1.0,1000.0,100.0)
        score=st.number_input("Score (0 if not graded)",0.0,1000.0,0.0)
        if st.form_submit_button("Add exam", type="primary"):
            if title.strip():
                db.execute("""INSERT INTO exams(title,subject_id,exam_date,exam_type,max_marks,score)
                              VALUES(?,?,?,?,?,?)""",
                           (title.strip(),options[subject],exam_date.isoformat(),exam_type,max_marks,score if score>0 else None))
                st.success("Exam added."); st.rerun()
            else: st.error("Exam title is required.")

# ---------- Notes ----------
elif page == "📒 Notes":
    st.title("📒 Notes & Knowledge Vault")
    notes = db.query("""SELECT n.id,n.title,n.content,n.created_at,COALESCE(s.name,'General') subject
                        FROM notes n LEFT JOIN subjects s ON s.id=n.subject_id ORDER BY n.created_at DESC""")
    for _,r in notes.iterrows():
        with st.expander(f"📌 {r['title']} — {r['subject']}"):
            st.caption(f"Created: {r['created_at']}")
            st.write(r["content"])
            if st.button("Delete note", key=f"note_{r['id']}"):
                db.execute("DELETE FROM notes WHERE id=?", (int(r["id"]),)); st.rerun()
    subjects=db.query("SELECT id,name FROM subjects ORDER BY name")
    options={"General":None}|{r["name"]:int(r["id"]) for _,r in subjects.iterrows()}
    with st.form("note_form"):
        title=st.text_input("Note title *")
        subject=st.selectbox("Subject",list(options))
        content=st.text_area("Write your note",height=180)
        if st.form_submit_button("Save note",type="primary"):
            if title.strip() and content.strip():
                db.execute("INSERT INTO notes(title,subject_id,content,created_at) VALUES(?,?,?,?)",
                           (title.strip(),options[subject],content.strip(),datetime.now().isoformat()))
                st.success("Note saved."); st.rerun()
            else: st.error("Title and content are required.")

# ---------- Goals ----------
elif page == "🎯 Goals":
    st.title("🎯 Goals & Milestones")
    goals=db.query("SELECT * FROM goals ORDER BY deadline")
    if not goals.empty:
        for _,r in goals.iterrows():
            pct=min(100,max(0,float(r["progress"])))
            st.write(f"**{r['title']}** — {pct:.0f}%")
            st.progress(pct/100)
            st.caption(f"Deadline: {r['deadline'] or 'Not set'}")
            a,b=st.columns([5,1])
            newp=a.slider("Progress",0,100,int(pct),key=f"prog_{r['id']}",label_visibility="collapsed")
            if b.button("🗑️",key=f"goaldel_{r['id']}"):
                db.execute("DELETE FROM goals WHERE id=?",(int(r["id"]),)); st.rerun()
            if newp != int(pct):
                db.execute("UPDATE goals SET progress=? WHERE id=?",(newp,int(r["id"])))
                st.rerun()
    with st.form("goal_form"):
        title=st.text_input("Goal title *")
        deadline=st.date_input("Deadline",date.today()+timedelta(days=30))
        if st.form_submit_button("Add goal",type="primary"):
            if title.strip():
                db.execute("INSERT INTO goals(title,deadline,progress) VALUES(?,?,0)",(title.strip(),deadline.isoformat()))
                st.success("Goal added."); st.rerun()
            else: st.error("Goal title is required.")

# ---------- Analytics ----------
elif page == "📊 Analytics":
    st.title("📊 Study Analytics")
    st.subheader("Log a study session")
    subjects=db.query("SELECT id,name FROM subjects ORDER BY name")
    options={"General":None}|{r["name"]:int(r["id"]) for _,r in subjects.iterrows()}
    with st.form("study_form"):
        a,b,c=st.columns(3)
        subject=a.selectbox("Subject",list(options))
        study_date=b.date_input("Date",date.today())
        hours=c.number_input("Hours studied",0.1,24.0,1.0,step=0.5)
        topic=st.text_input("Topic / activity")
        if st.form_submit_button("Log session",type="primary"):
            db.execute("""INSERT INTO study_sessions(subject_id,study_date,hours,topic)
                          VALUES(?,?,?,?)""",(options[subject],study_date.isoformat(),hours,topic.strip()))
            st.success("Study session logged."); st.rerun()

    st.subheader("Performance overview")
    c1,c2=st.columns(2)
    with c1:
        weekly=get_weekly_study()
        if not weekly.empty: st.line_chart(weekly.set_index("day")["hours"],height=300)
        else: st.info("No study data yet.")
    with c2:
        perf=get_subject_performance()
        if not perf.empty: st.bar_chart(perf.set_index("subject")["score"],height=300)
        else: st.info("No scored exams yet.")

    st.subheader("Task completion")
    ts=get_task_summary()
    if not ts.empty: st.dataframe(ts,use_container_width=True,hide_index=True)

    st.subheader("Study history")
    history=db.query("""SELECT ss.study_date,COALESCE(s.name,'General') subject,ss.hours,ss.topic
                        FROM study_sessions ss LEFT JOIN subjects s ON s.id=ss.subject_id
                        ORDER BY ss.study_date DESC,ss.id DESC LIMIT 100""")
    st.dataframe(history,use_container_width=True,hide_index=True)

# ---------- Settings ----------
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    name=st.text_input("Student name",profile.get("student_name","Student"))
    semester=st.text_input("Semester / Year",profile.get("semester","B.Tech 3rd Year"))
    college=st.text_input("College",profile.get("college",""))
    target=st.number_input("Default target score (%)",0.0,100.0,float(profile.get("target_score",75)))
    if st.button("Save settings",type="primary"):
        db.set_setting("student_name",name.strip())
        db.set_setting("semester",semester.strip())
        db.set_setting("college",college.strip())
        db.set_setting("target_score",str(target))
        st.success("Settings saved.")
    st.divider()
    st.subheader("Database")
    st.caption("Your data is stored locally in data/study.db.")
    if st.button("⚠️ Reset all data"):
        st.session_state["confirm_reset"]=True
    if st.session_state.get("confirm_reset"):
        st.warning("This permanently deletes all subjects, tasks, attendance, exams, notes, goals and study sessions.")
        a,b=st.columns(2)
        if a.button("Yes, reset database",type="primary"):
            db.reset()
            st.session_state["confirm_reset"]=False
            st.success("Database reset.")
            st.rerun()
        if b.button("Cancel"):
            st.session_state["confirm_reset"]=False
            st.rerun()
