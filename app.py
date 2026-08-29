from flask import Flask, render_template
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from config import Config
from database.db import db

from routes.auth import auth

from models.user import User
from models.department import Department
from models.student import Student
from models.teacher import Teacher
from models.attendance import Attendance
from models.result import Result

from routes.admin import admin
from routes.teacher import teacher
from routes.student import student
from routes.student_management import student_management
from routes.teacher_management import teacher_management
from routes.analytics import analytics
from routes.prediction import prediction

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(teacher)
app.register_blueprint(student)
app.register_blueprint(student_management)
app.register_blueprint(teacher_management)
app.register_blueprint(analytics)
app.register_blueprint(prediction)


@app.route("/")
def home():
    return render_template("index.html")


def initialize_database():
    """Create tables and safely add student login credentials to an existing DB."""
    db.create_all()

    inspector = inspect(db.engine)
    student_columns = {column["name"] for column in inspector.get_columns("students")}

    if "password_hash" not in student_columns:
        db.session.execute(
            text("ALTER TABLE students ADD COLUMN password_hash VARCHAR(255) NULL")
        )
        db.session.commit()

    # Existing students receive Student ID as their temporary password.
    # This runs only for students that do not already have a password.
    students = Student.query.filter(
        (Student.password_hash.is_(None)) | (Student.password_hash == "")
    ).all()
    for student in students:
        student.password_hash = generate_password_hash(student.student_id)
    if students:
        db.session.commit()


with app.app_context():
    initialize_database()


if __name__ == "__main__":
    app.run(debug=True)