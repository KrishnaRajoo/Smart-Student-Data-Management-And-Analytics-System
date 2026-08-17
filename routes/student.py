from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from database.db import db
from models.student import Student
from models.result import Result
from models.attendance import Attendance
from werkzeug.security import generate_password_hash

student = Blueprint("student", __name__)


def _current_student():
    if session.get("role") != "student" or not session.get("student_id"):
        return None
    return db.session.get(Student, session["student_id"])


def _guard():
    s = _current_student()
    return s if s else redirect(url_for("auth.login", role="student"))


def _attendance_data(s):
    records = Attendance.query.filter_by(student_id=s.id).order_by(
        Attendance.attendance_date.desc(), Attendance.id.desc()
    ).all()
    total = len(records)
    present = sum(1 for r in records if str(r.status).lower() == "present")
    percentage = round((present / total) * 100, 2) if total else round(s.attendance or 0, 2)
    return records, total, present, percentage


def _performance_data(s):
    results = Result.query.filter_by(student_id=s.id).order_by(
        Result.semester, Result.subject
    ).all()

    semester_map = {}
    for r in results:
        pct = (r.marks / r.max_marks) * 100 if r.max_marks else 0
        semester_map.setdefault(r.semester, []).append(pct)

    semester_labels = sorted(semester_map)
    semester_values = [
        round(sum(semester_map[sem]) / len(semester_map[sem]), 2)
        for sem in semester_labels
    ]

    subject_rows = []
    for r in results:
        pct = round((r.marks / r.max_marks) * 100, 2) if r.max_marks else 0
        subject_rows.append({
            "semester": r.semester,
            "subject": r.subject,
            "marks": r.marks,
            "max_marks": r.max_marks,
            "percentage": pct,
        })

    average_marks = round(sum(semester_values) / len(semester_values), 2) if semester_values else 0
    highest = max(subject_rows, key=lambda x: x["percentage"], default=None)
    lowest = min(subject_rows, key=lambda x: x["percentage"], default=None)

    return results, semester_labels, semester_values, subject_rows, average_marks, highest, lowest


def _performance_label(cgpa):
    cgpa = cgpa or 0
    if cgpa >= 9:
        return "Excellent"
    if cgpa >= 7.5:
        return "Good"
    if cgpa >= 6:
        return "Needs Improvement"
    return "At Risk"


@student.route("/student/dashboard")
def dashboard():
    s = _guard()
    if not isinstance(s, Student):
        return s

    results, semester_labels, semester_values, subject_rows, average_marks, highest, lowest = _performance_data(s)
    records, total_attendance, present_days, attendance_pct = _attendance_data(s)

    return render_template(
        "student/dashboard.html",
        student=s,
        results=results,
        total_attendance=total_attendance,
        present_days=present_days,
        attendance_pct=attendance_pct,
        semester_labels=semester_labels,
        semester_values=semester_values,
        performance=_performance_label(s.cgpa),
        average_marks=average_marks,
        highest=highest,
        lowest=lowest,
        recent_attendance=records[:7],
    )


@student.route("/student/performance")
def performance():
    s = _guard()
    if not isinstance(s, Student):
        return s

    results, semester_labels, semester_values, subject_rows, average_marks, highest, lowest = _performance_data(s)
    _, total_attendance, present_days, attendance_pct = _attendance_data(s)

    return render_template(
        "student/performance.html",
        student=s,
        results=results,
        subject_rows=subject_rows,
        semester_labels=semester_labels,
        semester_values=semester_values,
        average_marks=average_marks,
        highest=highest,
        lowest=lowest,
        attendance_pct=attendance_pct,
        performance=_performance_label(s.cgpa),
    )


@student.route("/student/attendance")
def attendance():
    s = _guard()
    if not isinstance(s, Student):
        return s

    records, total, present, percentage = _attendance_data(s)
    return render_template(
        "student/attendance.html",
        student=s,
        records=records,
        total=total,
        present=present,
        absent=total - present,
        percentage=percentage,
    )


@student.route("/student/academic-records")
def academic_records():
    s = _guard()
    if not isinstance(s, Student):
        return s

    results, semester_labels, semester_values, subject_rows, average_marks, highest, lowest = _performance_data(s)
    return render_template(
        "student/academic_records.html",
        student=s,
        results=results,
        subject_rows=subject_rows,
        average_marks=average_marks,
    )


@student.route("/student/profile")
def profile():
    s = _guard()
    if not isinstance(s, Student):
        return s
    return render_template("student/profile.html", student=s)


@student.route("/student/change-password", methods=["POST"])
def change_password():
    s = _guard()
    if not isinstance(s, Student):
        return s

    current = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")

    if not s.check_password(current):
        flash("Current password is incorrect.", "danger")
    elif len(new_password) < 6:
        flash("New password must contain at least 6 characters.", "danger")
    elif new_password != confirm:
        flash("New passwords do not match.", "danger")
    else:
        s.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("Password updated successfully.", "success")

    return redirect(url_for("student.profile"))
