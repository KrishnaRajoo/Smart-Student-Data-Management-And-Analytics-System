from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for
)

from models.user import User
from models.teacher import Teacher
from models.student import Student

from werkzeug.security import check_password_hash

auth = Blueprint("auth", __name__)


@auth.route("/login")
def login_selection():
    return render_template("auth/login_selection.html")


@auth.route("/login/<role>", methods=["GET", "POST"])
def login(role):

    roles = {
        "admin": {
            "title": "Administrator Login",
            "icon": "fa-user-shield",
            "color": "#2563eb"
        },
        "teacher": {
            "title": "Teacher Login",
            "icon": "fa-chalkboard-user",
            "color": "#22c55e"
        },
        "student": {
            "title": "Student Login",
            "icon": "fa-user-graduate",
            "color": "#7c3aed"
        }
    }

    if role not in roles:
        return "Invalid Role", 404

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

    # ---------------- ADMIN LOGIN ---------------- #

        if role == "admin":

            user = User.query.filter_by(
                username=username,
                role="admin"
            ).first()

            if user and user.check_password(password):

                session.clear()

                session["user_id"] = user.id
                session["role"] = "admin"
                session["username"] = user.username

                return redirect(
                    url_for("admin.dashboard")
                )

    # ---------------- TEACHER LOGIN ---------------- #

        elif role == "teacher":

            teacher = Teacher.query.filter_by(
                teacher_id=username
            ).first()

            if teacher and check_password_hash(
                teacher.password,
                password
            ):

                session.clear()

                session["teacher_id"] = teacher.id
                session["role"] = "teacher"

                session["teacher_name"] = (
                    teacher.first_name + " " +
                    teacher.last_name
                )

                return redirect(
                    url_for("teacher.dashboard")
                )

    # ---------------- STUDENT LOGIN ---------------- #

        elif role == "student":

            student = Student.query.filter_by(
                student_id=username
            ).first()

            if student:

                flash(
                    "Student portal will be implemented next.",
                    "info"
                )

                return redirect(
                    url_for("auth.login", role="student")
                )

        flash(
            "Invalid username or password.",
            "danger"
        )

    return render_template(
        "auth/login.html",
        role=role,
        data=roles[role]
    )
@auth.route("/logout")
def logout():

    session.clear()

    return render_template("index.html")
