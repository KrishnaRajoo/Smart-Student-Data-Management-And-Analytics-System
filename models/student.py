from database.db import db
from werkzeug.security import generate_password_hash, check_password_hash


class Student(db.Model):

    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.String(30), unique=True, nullable=False)

    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))

    email = db.Column(db.String(150), unique=True)
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

    # Student login credential. Existing students are initialized
    # with their Student ID as the temporary password.
    password_hash = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    department = db.relationship(
        "Department",
        back_populates="students"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(
            self.password_hash
            and check_password_hash(self.password_hash, password)
        )

    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()
