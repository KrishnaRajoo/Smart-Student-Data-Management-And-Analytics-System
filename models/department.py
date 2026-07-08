from database.db import db

class Department(db.Model):

    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)

    department_code = db.Column(
        db.String(10),
        unique=True,
        nullable=False
    )

    department_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    hod_name = db.Column(db.String(100))

    students = db.relationship(
        "Student",
        backref="department",
        lazy=True
    )
    students = db.relationship(
        "Student",
        back_populates="department"
    )

    teachers = db.relationship(
        "Teacher",
        back_populates="department",
        cascade="all, delete"
    )
    def __repr__(self):
        return f"<Department {self.department_name}>"