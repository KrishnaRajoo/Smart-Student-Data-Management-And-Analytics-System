from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from sqlalchemy import or_
from database.db import db
from models.teacher import Teacher
from models.student import Student
from models.attendance import Attendance
from models.result import Result

teacher = Blueprint("teacher", __name__)

def _teacher():
    if session.get("role") != "teacher" or not session.get("teacher_id"):
        return None
    t = db.session.get(Teacher, session["teacher_id"])
    return t if t and str(t.status).lower() == "active" else None

def _guard():
    t = _teacher()
    return t if t else redirect(url_for("auth.login", role="teacher"))

def _student(t, sid):
    return Student.query.filter_by(id=sid, department_id=t.department_id).first()

def _attendance_pct(sid):
    total = Attendance.query.filter_by(student_id=sid).count()
    if not total: return None
    present = Attendance.query.filter_by(student_id=sid, status="Present").count()
    return round(present / total * 100, 2)

@teacher.route("/teacher/dashboard")
def dashboard():
    t = _guard()
    if not isinstance(t, Teacher): return t
    students = Student.query.filter_by(department_id=t.department_id).all()
    n = len(students)
    avg_cgpa = round(sum((s.cgpa or 0) for s in students)/n, 2) if n else 0
    avg_att = round(sum((s.attendance or 0) for s in students)/n, 2) if n else 0
    best = sorted(students, key=lambda s:s.cgpa or 0, reverse=True)[:5]
    risk = sorted([s for s in students if (s.cgpa or 0)<6.5 or (s.attendance or 0)<75], key=lambda s:(s.cgpa or 0,s.attendance or 0))[:5]
    by_sem = {}
    for s in students: by_sem.setdefault(s.semester or 0, []).append(s.cgpa or 0)
    labels=sorted(by_sem); values=[round(sum(by_sem[x])/len(by_sem[x]),2) for x in labels]
    return render_template("teacher/dashboard.html", teacher=t,total_students=n,avg_cgpa=avg_cgpa,avg_attendance=avg_att,best_students=best,at_risk=risk,semester_labels=labels,semester_values=values)

@teacher.route("/teacher/students")
def students():
    t=_guard()
    if not isinstance(t, Teacher): return t
    search=request.args.get("search","").strip(); semester=request.args.get("semester","").strip(); performance=request.args.get("performance","").strip()
    q=Student.query.filter_by(department_id=t.department_id)
    if search:
        term=f"%{search}%"; q=q.filter(or_(Student.student_id.ilike(term),Student.first_name.ilike(term),Student.last_name.ilike(term)))
    if semester: q=q.filter(Student.semester==int(semester))
    if performance=="excellent": q=q.filter(Student.cgpa>=9)
    elif performance=="good": q=q.filter(Student.cgpa>=7,Student.cgpa<9)
    elif performance=="needs_attention": q=q.filter(or_(Student.cgpa<7,Student.attendance<75))
    students=q.order_by(Student.student_id).all()
    semesters=[x[0] for x in db.session.query(Student.semester).filter(Student.department_id==t.department_id,Student.semester.isnot(None)).distinct().order_by(Student.semester).all()]
    return render_template("teacher/students.html",teacher=t,students=students,semesters=semesters,search=search,selected_semester=semester,performance=performance)

@teacher.route("/teacher/students/<int:student_id>",methods=["GET","POST"])
def student_detail(student_id):
    t=_guard()
    if not isinstance(t, Teacher): return t
    s=_student(t,student_id)
    if not s: flash("Student not found in your department.","danger"); return redirect(url_for("teacher.students"))
    if request.method=="POST":
        try:
            cgpa=float(request.form["cgpa"]); sem=int(request.form["semester"])
            if not 0<=cgpa<=10 or sem<1: raise ValueError
            s.cgpa=cgpa; s.semester=sem; db.session.commit(); flash("Student academic details updated successfully.","success")
        except (ValueError,TypeError): db.session.rollback(); flash("Please enter valid academic values.","danger")
        return redirect(url_for("teacher.student_detail",student_id=s.id))
    results=Result.query.filter_by(student_id=s.id).order_by(Result.semester,Result.subject).all()
    return render_template("teacher/student_detail.html",teacher=t,student=s,results=results)

@teacher.route("/teacher/students/<int:student_id>/results",methods=["POST"])
def update_result(student_id):
    t=_guard()
    if not isinstance(t, Teacher): return t
    s=_student(t,student_id)
    if not s: flash("Student not found in your department.","danger"); return redirect(url_for("teacher.students"))
    try:
        sem=int(request.form["semester"]); subject=request.form["subject"].strip(); marks=float(request.form["marks"]); max_marks=float(request.form.get("max_marks",100))
        if not subject or sem<1 or max_marks<=0 or marks<0 or marks>max_marks: raise ValueError
        rid=request.form.get("result_id"); r=db.session.get(Result,int(rid)) if rid else None
        if r and r.student_id!=s.id: r=None
        if not r: r=Result(student_id=s.id,semester=sem,subject=subject); db.session.add(r)
        r.semester=sem;r.subject=subject;r.marks=marks;r.max_marks=max_marks;db.session.commit();flash("Marks updated successfully.","success")
    except (ValueError,TypeError): db.session.rollback();flash("Enter valid marks, semester and maximum marks.","danger")
    return redirect(url_for("teacher.student_detail",student_id=s.id))

@teacher.route("/teacher/attendance",methods=["GET","POST"])
def attendance():
    t=_guard()
    if not isinstance(t, Teacher): return t
    selected_date=request.values.get("date",date.today().isoformat()); selected_semester=request.values.get("semester","")
    try: att_date=date.fromisoformat(selected_date)
    except ValueError: att_date=date.today();selected_date=att_date.isoformat()
    if request.method=="POST":
        try:
            for raw in request.form.getlist("student_id"):
                s=_student(t,int(raw))
                if not s: continue
                status=request.form.get(f"status_{s.id}","Absent"); status=status if status in {"Present","Absent"} else "Absent"
                r=Attendance.query.filter_by(student_id=s.id,teacher_id=t.id,attendance_date=att_date).first()
                if r:r.status=status
                else:db.session.add(Attendance(student_id=s.id,teacher_id=t.id,attendance_date=att_date,status=status))
            db.session.commit()
            for s in Student.query.filter_by(department_id=t.department_id).all():
                pct=_attendance_pct(s.id)
                if pct is not None:s.attendance=pct
            db.session.commit();flash("Attendance saved successfully.","success")
        except Exception: db.session.rollback();flash("Unable to save attendance. Please try again.","danger")
    q=Student.query.filter_by(department_id=t.department_id)
    if selected_semester:q=q.filter(Student.semester==int(selected_semester))
    students=q.order_by(Student.student_id).all()
    existing={r.student_id:r.status for r in Attendance.query.filter_by(teacher_id=t.id,attendance_date=att_date).all()}
    semesters=[x[0] for x in db.session.query(Student.semester).filter(Student.department_id==t.department_id,Student.semester.isnot(None)).distinct().order_by(Student.semester).all()]
    return render_template("teacher/attendance.html",teacher=t,students=students,existing=existing,selected_date=selected_date,selected_semester=selected_semester,semesters=semesters)

@teacher.route("/teacher/performance")
def performance():
    t=_guard()
    if not isinstance(t, Teacher): return t
    students=sorted(Student.query.filter_by(department_id=t.department_id).all(),key=lambda s:s.cgpa or 0,reverse=True)
    n=len(students);avg_cgpa=round(sum((s.cgpa or 0) for s in students)/n,2) if n else 0;avg_att=round(sum((s.attendance or 0) for s in students)/n,2) if n else 0
    return render_template("teacher/performance.html",teacher=t,students=students,avg_cgpa=avg_cgpa,avg_attendance=avg_att)

@teacher.route("/teacher/profile")
def profile():
    t=_guard()
    if not isinstance(t, Teacher): return t
    return render_template("teacher/profile.html",teacher=t)
