from database.db import db


class Teacher(db.Model):

    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)

    teacher_id = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    phone = db.Column(db.String(20))

    password = db.Column(db.String(255), nullable=False)

    gender = db.Column(db.String(20))

    designation = db.Column(
        db.String(100),
        nullable=False
    )

    qualification = db.Column(
        db.String(100)
    )

    joining_date = db.Column(db.Date)

    status = db.Column(
        db.String(20),
        default="Active"
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    department = db.relationship(
        "Department",
        back_populates="teachers"
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Teacher {self.teacher_id}>"