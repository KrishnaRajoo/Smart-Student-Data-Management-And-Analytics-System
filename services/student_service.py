from database.db import db
from models.student import Student


class StudentService:

    @staticmethod
    def get_all_students():

        return Student.query.order_by(
            Student.student_id
        ).all()

    @staticmethod
    def get_student(student_id):

        return Student.query.get(student_id)

    @staticmethod
    def create_student(data):

        student = Student(

            student_id=data["student_id"],

            first_name=data["first_name"],

            last_name=data["last_name"],

            email=data["email"],

            phone=data["phone"],

            gender=data["gender"],

            semester=int(data["semester"]),

            cgpa=float(data["cgpa"]),

            attendance=float(data["attendance"]),

            department_id=int(data["department_id"]),

            password_hash=None

        )

        # Initial student password is the Student ID.
        student.set_password(data["student_id"])

        db.session.add(student)

        db.session.commit()

        return student

    @staticmethod
    def delete_student(student_id):

        student = Student.query.get(student_id)

        if student:

            db.session.delete(student)

            db.session.commit()

            return True

        return False