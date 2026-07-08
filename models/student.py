from database.db import db


class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    first_name = db.Column(db.String(100))

    last_name = db.Column(db.String(100))

    email = db.Column(
        db.String(150),
        unique=True
    )

    phone = db.Column(db.String(20))

    gender = db.Column(db.String(20))

    semester = db.Column(db.Integer)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    cgpa = db.Column(db.Float)

    attendance = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
    department = db.relationship(
        "Department",
        back_populates="students"
    )