from database.db import db
class Result(db.Model):
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False, index=True)
    semester = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    student = db.relationship("Student", backref=db.backref("results", lazy=True))
