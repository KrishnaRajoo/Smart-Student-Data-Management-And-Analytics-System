"""
======================================================================
SMART STUDENT ANALYTICS SYSTEM
ACADEMIC RISK PREDICTION ROUTES
======================================================================

Prediction pages:

    /student/prediction
    /teacher/prediction
    /admin/prediction

MODEL FEATURES
--------------

The trained model uses ONLY these six features:

    1. semester
    2. cgpa
    3. attendance
    4. average_marks
    5. highest_marks
    6. lowest_marks

The three marks-based features are calculated from ACTUAL
Result records stored in the SSAS database.

No synthetic academic data is inserted into the application
database.

NOT USED:

    - assignment marks
    - internal marks
    - quiz marks
    - study hours
    - assignment score
    - internal examination score

======================================================================
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from database.db import db

from models.student import Student
from models.teacher import Teacher
from models.result import Result

from services.prediction_service import predict


# ======================================================================
# BLUEPRINT
# ======================================================================

prediction = Blueprint(
    "prediction",
    __name__
)


# ======================================================================
# SHARED TEMPLATE
# ======================================================================

PREDICTION_TEMPLATE = "prediction/prediction.html"


# ======================================================================
# TEACHER HELPERS
# ======================================================================

def _teacher():
    """
    Get the currently logged-in teacher.

    This follows the same authentication architecture
    used by routes/teacher.py.
    """

    if (
        session.get("role") != "teacher"
        or not session.get("teacher_id")
    ):
        return None

    teacher = db.session.get(
        Teacher,
        session["teacher_id"]
    )

    if (
        teacher
        and str(teacher.status).lower() == "active"
    ):
        return teacher

    return None


def _teacher_guard():
    """
    Protect teacher prediction route.
    """

    teacher = _teacher()

    if teacher:
        return teacher

    return redirect(
        url_for(
            "auth.login",
            role="teacher"
        )
    )


# ======================================================================
# ADMIN HELPERS
# ======================================================================

def _admin_guard():
    """
    Protect admin prediction route.

    The existing application uses session["role"]
    for role identification.
    """

    if session.get("role") != "admin":

        return redirect(
            url_for(
                "auth.login",
                role="admin"
            )
        )

    return True


# ======================================================================
# STUDENT HELPERS
# ======================================================================

def _student_from_id(student_id):
    """
    Find a student using the database primary key.
    """

    if not student_id:
        return None

    try:

        return db.session.get(
            Student,
            int(student_id)
        )

    except (
        TypeError,
        ValueError
    ):

        return None


def _logged_in_student():
    """
    Retrieve the student associated with the current
    student session.

    The application is expected to store:

        session["student_id"]

    """

    if session.get("role") != "student":
        return None

    student_id = session.get(
        "student_id"
    )

    if not student_id:
        return None

    return _student_from_id(
        student_id
    )


# ======================================================================
# RESULT STATISTICS
# ======================================================================

def _calculate_result_statistics(student):
    """
    Calculate academic result statistics from REAL
    Result records.

    Returns:

        average_marks
        highest_marks
        lowest_marks
        result_count

    Marks are normalized to percentages using:

        marks / max_marks * 100

    No artificial values are generated.
    """

    results = (
        Result.query
        .filter_by(
            student_id=student.id
        )
        .all()
    )

    percentages = []


    for result in results:

        marks = getattr(
            result,
            "marks",
            None
        )

        max_marks = getattr(
            result,
            "max_marks",
            None
        )


        if marks is None:
            continue

        if max_marks is None:
            continue


        try:

            marks = float(
                marks
            )

            max_marks = float(
                max_marks
            )

        except (
            TypeError,
            ValueError
        ):

            continue


        if max_marks <= 0:
            continue


        percentage = (
            marks / max_marks
        ) * 100


        # Keep percentages within valid academic range.

        percentage = max(
            0.0,
            min(
                100.0,
                percentage
            )
        )


        percentages.append(
            percentage
        )


    if not percentages:

        return {
            "average_marks": None,
            "highest_marks": None,
            "lowest_marks": None,
            "result_count": 0
        }


    return {
        "average_marks": round(
            sum(percentages) / len(percentages),
            2
        ),

        "highest_marks": round(
            max(percentages),
            2
        ),

        "lowest_marks": round(
            min(percentages),
            2
        ),

        "result_count": len(
            percentages
        )
    }


# ======================================================================
# SEMESTER
# ======================================================================

def _get_semester(student):
    """
    Get the student's current semester.

    Primary source:

        Student.semester

    If unavailable, the latest semester from actual
    Result records is used.
    """

    semester = getattr(
        student,
        "semester",
        None
    )


    if semester is not None:

        try:

            return int(
                float(semester)
            )

        except (
            TypeError,
            ValueError
        ):

            pass


    # --------------------------------------------------------------
    # Fallback: latest actual result semester
    # --------------------------------------------------------------

    results = (
        Result.query
        .filter_by(
            student_id=student.id
        )
        .all()
    )


    semesters = []


    for result in results:

        value = getattr(
            result,
            "semester",
            None
        )


        if value is None:
            continue


        try:

            semesters.append(
                int(
                    float(value)
                )
            )

        except (
            TypeError,
            ValueError
        ):

            continue


    if semesters:

        return max(
            semesters
        )


    return None


# ======================================================================
# BUILD FEATURES
# ======================================================================

def _build_features(student):
    """
    Build the exact six-feature input expected by the
    trained model.

    IMPORTANT:

    The keys here MUST match the features used during
    model training.
    """

    statistics = _calculate_result_statistics(
        student
    )


    semester = _get_semester(
        student
    )


    cgpa = getattr(
        student,
        "cgpa",
        None
    )


    attendance = getattr(
        student,
        "attendance",
        None
    )


    features = {

        "semester": semester,

        "cgpa": cgpa,

        "attendance": attendance,

        "average_marks": statistics[
            "average_marks"
        ],

        "highest_marks": statistics[
            "highest_marks"
        ],

        "lowest_marks": statistics[
            "lowest_marks"
        ]
    }


    return (
        features,
        statistics
    )


# ======================================================================
# VALIDATE FEATURES
# ======================================================================

def _missing_features(features):
    """
    Return a list of missing model inputs.
    """

    missing = []


    required = [

        "semester",
        "cgpa",
        "attendance",
        "average_marks",
        "highest_marks",
        "lowest_marks"

    ]


    for feature in required:

        value = features.get(
            feature
        )

        if value is None:

            missing.append(
                feature
            )


    return missing


# ======================================================================
# GENERATE PREDICTION
# ======================================================================

def _generate_prediction(student):
    """
    Generate prediction for a single student.

    Returns a dictionary suitable for prediction.html.
    """

    features, statistics = _build_features(
        student
    )


    missing = _missing_features(
        features
    )


    # --------------------------------------------------------------
    # Insufficient database data
    # --------------------------------------------------------------

    if missing:

        return {

            "status": "insufficient_data",

            "risk_level": None,

            "prediction": None,

            "confidence": None,

            "probabilities": {},

            "recommendations": [],

            "model": None,

            "model_version": None,

            "features": features,

            "result_count": statistics[
                "result_count"
            ],

            "missing_features": missing
        }


    # --------------------------------------------------------------
    # Model prediction
    # --------------------------------------------------------------

    try:

        result = predict(
            features
        )


    except Exception as exc:

        return {

            "status": "error",

            "risk_level": None,

            "prediction": None,

            "confidence": None,

            "probabilities": {},

            "recommendations": [],

            "model": None,

            "model_version": None,

            "features": features,

            "result_count": statistics[
                "result_count"
            ],

            "error": str(
                exc
            )
        }


    # --------------------------------------------------------------
    # Normalize result
    # --------------------------------------------------------------

    result = dict(
        result
    )


    result.setdefault(
        "status",
        "success"
    )

    result.setdefault(
        "probabilities",
        {}
    )

    result.setdefault(
        "recommendations",
        []
    )

    result.setdefault(
        "model",
        "Unknown"
    )

    result.setdefault(
        "model_version",
        "1.0"
    )

    result.setdefault(
        "confidence",
        0
    )


    result["features"] = features

    result["result_count"] = statistics[
        "result_count"
    ]


    return result


# ======================================================================
# STUDENT LIST
# ======================================================================

def _all_students():
    """
    Return all students for administrator prediction.
    """

    return (
        Student.query
        .order_by(
            Student.student_id
        )
        .all()
    )


# ======================================================================
# TEACHER STUDENTS
# ======================================================================

def _teacher_students(teacher):
    """
    Return only students belonging to the teacher's
    department.

    This matches the existing teacher route architecture.
    """

    return (
        Student.query
        .filter_by(
            department_id=teacher.department_id
        )
        .order_by(
            Student.student_id
        )
        .all()
    )


# ======================================================================
# STUDENT PREDICTION
# ======================================================================

@prediction.route(
    "/student/prediction",
    methods=["GET"]
)
def student_prediction():

    student = _logged_in_student()


    if student is None:

        return redirect(
            url_for(
                "auth.login",
                role="student"
            )
        )


    prediction_result = _generate_prediction(
        student
    )


    return render_template(

        PREDICTION_TEMPLATE,

        role="student",

        # ----------------------------------------------------------
        # Required by student_base.html
        # ----------------------------------------------------------

        student=student,

        # ----------------------------------------------------------
        # Prediction
        # ----------------------------------------------------------

        prediction=prediction_result,

        features=prediction_result.get(
            "features",
            {}
        ),

        # ----------------------------------------------------------
        # Student layout compatibility
        # ----------------------------------------------------------

        students=[],

        teacher=None,

        results=[],

        summary=None
    )


# ======================================================================
# TEACHER PREDICTION
# ======================================================================

@prediction.route(
    "/teacher/prediction",
    methods=["GET"]
)
def teacher_prediction():

    teacher = _teacher_guard()


    if not isinstance(
        teacher,
        Teacher
    ):

        return teacher


    # --------------------------------------------------------------
    # ONLY students in teacher's department
    # --------------------------------------------------------------

    students = _teacher_students(
        teacher
    )


    selected_student_id = request.args.get(
        "student_id"
    )


    student = None

    prediction_result = None


    # --------------------------------------------------------------
    # Selected student
    # --------------------------------------------------------------

    if selected_student_id:

        student = _student_from_id(
            selected_student_id
        )


        # ----------------------------------------------------------
        # SECURITY:
        #
        # Never allow teacher to predict students from
        # another department.
        # ----------------------------------------------------------

        if (
            student is not None
            and student.department_id
            != teacher.department_id
        ):

            flash(
                "Student not found in your department.",
                "danger"
            )

            return redirect(
                url_for(
                    "prediction.teacher_prediction"
                )
            )


        if student is not None:

            prediction_result = (
                _generate_prediction(
                    student
                )
            )


    # --------------------------------------------------------------
    # Features
    # --------------------------------------------------------------

    features = (

        prediction_result.get(
            "features",
            {}
        )

        if prediction_result

        else {}
    )


    return render_template(

        PREDICTION_TEMPLATE,

        role="teacher",

        # ----------------------------------------------------------
        # REQUIRED BY teacher_base.html
        # ----------------------------------------------------------

        teacher=teacher,

        # ----------------------------------------------------------
        # Prediction page
        # ----------------------------------------------------------

        student=student,

        students=students,

        prediction=prediction_result,

        features=features,

        results=[],

        summary=None
    )


# ======================================================================
# ADMIN PREDICTION
# ======================================================================

@prediction.route(
    "/admin/prediction",
    methods=["GET"]
)
def admin_prediction():

    authorized = _admin_guard()


    if authorized is not True:

        return authorized


    # --------------------------------------------------------------
    # All students available to admin
    # --------------------------------------------------------------

    students = _all_students()


    selected_student_id = request.args.get(
        "student_id"
    )


    student = None

    prediction_result = None


    # --------------------------------------------------------------
    # Selected student
    # --------------------------------------------------------------

    if selected_student_id:

        student = _student_from_id(
            selected_student_id
        )


        if student is not None:

            prediction_result = (
                _generate_prediction(
                    student
                )
            )


    # --------------------------------------------------------------
    # Features
    # --------------------------------------------------------------

    features = (

        prediction_result.get(
            "features",
            {}
        )

        if prediction_result

        else {}
    )


    return render_template(

        PREDICTION_TEMPLATE,

        role="admin",

        # ----------------------------------------------------------
        # Admin layout
        # ----------------------------------------------------------

        student=student,

        students=students,

        teacher=None,

        # ----------------------------------------------------------
        # Prediction
        # ----------------------------------------------------------

        prediction=prediction_result,

        features=features,

        results=[],

        summary=None
    )
