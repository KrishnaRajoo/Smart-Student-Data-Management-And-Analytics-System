"""
======================================================================
SMART STUDENT ANALYTICS SYSTEM
Student Academic Risk Prediction Service
======================================================================

Purpose
-------
Provides a single prediction service used by the Flask application.

The service loads the trained ML artifact and predicts academic risk
using ONLY the actual academic features used by the current model.

MODEL FEATURES
--------------
    semester
    cgpa
    attendance
    average_marks
    highest_marks
    lowest_marks

PREDICTION CLASSES
------------------
    Low
    Moderate
    High

The service does NOT use:
    - assignment marks
    - internal marks
    - quiz marks
    - study hours
    - project marks
    - extracurricular scores
======================================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import pandas as pd


# ======================================================================
# PATH CONFIGURATION
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR
    / "ml"
    / "models"
    / "student_risk_model.pkl"
)

METRICS_PATH = (
    BASE_DIR
    / "ml"
    / "models"
    / "model_metrics.json"
)

FEATURES_PATH = (
    BASE_DIR
    / "ml"
    / "models"
    / "model_features.json"
)


# ======================================================================
# MODEL FEATURES
# ======================================================================

FEATURE_COLUMNS = [
    "semester",
    "cgpa",
    "attendance",
    "average_marks",
    "highest_marks",
    "lowest_marks"
]


# ======================================================================
# VALID RISK LABELS
# ======================================================================

VALID_RISK_LEVELS = {
    "Low",
    "Moderate",
    "High"
}


# ======================================================================
# MODEL CACHE
# ======================================================================

_MODEL_ARTIFACT = None


# ======================================================================
# LOAD MODEL
# ======================================================================

def load_model() -> Dict[str, Any]:
    """
    Load the trained prediction artifact.

    The current train_model.py saves:

        {
            "model": trained_pipeline,
            "label_encoder": label_encoder,
            "feature_columns": [...],
            "target_column": "...",
            "class_labels": [...]
        }

    The artifact is cached after the first load.
    """

    global _MODEL_ARTIFACT

    if _MODEL_ARTIFACT is not None:
        return _MODEL_ARTIFACT

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            "\nStudent risk model not found.\n\n"
            f"Expected location:\n{MODEL_PATH}\n\n"
            "Train the model first using:\n"
            "python ml/train_model.py"
        )

    artifact = joblib.load(
        MODEL_PATH
    )

    # --------------------------------------------------------------
    # Validate artifact
    # --------------------------------------------------------------

    if not isinstance(
        artifact,
        dict
    ):

        raise ValueError(
            "Invalid model artifact format. "
            "Expected a dictionary."
        )

    if "model" not in artifact:

        raise ValueError(
            "Model artifact does not contain "
            "the trained model."
        )

    if "label_encoder" not in artifact:

        raise ValueError(
            "Model artifact does not contain "
            "the label encoder."
        )

    _MODEL_ARTIFACT = artifact

    return _MODEL_ARTIFACT


# ======================================================================
# LOAD MODEL METRICS
# ======================================================================

def load_model_metrics() -> Dict[str, Any]:
    """
    Load saved model evaluation metrics.

    This is informational and is not required for prediction.
    """

    if not METRICS_PATH.exists():

        return {}

    try:

        with open(
            METRICS_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


# ======================================================================
# LOAD FEATURE METADATA
# ======================================================================

def load_feature_metadata() -> Dict[str, Any]:
    """
    Load feature metadata generated during training.
    """

    if not FEATURES_PATH.exists():

        return {}

    try:

        with open(
            FEATURES_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


# ======================================================================
# VALIDATE INPUT
# ======================================================================

def validate_input(
    data: Dict[str, Any]
) -> Dict[str, float]:
    """
    Validate and normalize prediction input.

    Only the six model features are accepted.

    Extra application/database fields are ignored so that a Student
    model object can safely be passed after extracting the required
    academic fields.
    """

    if not isinstance(
        data,
        dict
    ):

        raise ValueError(
            "Prediction input must be a dictionary."
        )


    normalized = {}


    # --------------------------------------------------------------
    # Required fields
    # --------------------------------------------------------------

    for feature in FEATURE_COLUMNS:

        if feature not in data:

            raise ValueError(
                f"Missing required prediction feature: "
                f"'{feature}'"
            )

        value = data[feature]

        if value is None:

            raise ValueError(
                f"Prediction feature '{feature}' "
                "cannot be None."
            )

        try:

            normalized[
                feature
            ] = float(value)

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                f"Prediction feature '{feature}' "
                f"must be numeric. Received: {value}"
            )


    # --------------------------------------------------------------
    # Semester
    # --------------------------------------------------------------

    if not 1 <= normalized["semester"] <= 8:

        raise ValueError(
            "Semester must be between 1 and 8."
        )


    # --------------------------------------------------------------
    # CGPA
    # --------------------------------------------------------------

    if not 0 <= normalized["cgpa"] <= 10:

        raise ValueError(
            "CGPA must be between 0 and 10."
        )


    # --------------------------------------------------------------
    # Attendance
    # --------------------------------------------------------------

    if not 0 <= normalized["attendance"] <= 100:

        raise ValueError(
            "Attendance must be between 0 and 100."
        )


    # --------------------------------------------------------------
    # Marks
    # --------------------------------------------------------------

    for feature in [
        "average_marks",
        "highest_marks",
        "lowest_marks"
    ]:

        if not 0 <= normalized[feature] <= 100:

            raise ValueError(
                f"{feature} must be between 0 and 100."
            )


    # --------------------------------------------------------------
    # Logical marks validation
    # --------------------------------------------------------------

    if (
        normalized["highest_marks"]
        <
        normalized["average_marks"]
    ):

        raise ValueError(
            "Highest marks cannot be lower than "
            "average marks."
        )


    if (
        normalized["lowest_marks"]
        >
        normalized["average_marks"]
    ):

        raise ValueError(
            "Lowest marks cannot be greater than "
            "average marks."
        )


    return normalized


# ======================================================================
# CREATE DATAFRAME
# ======================================================================

def create_feature_dataframe(
    data: Dict[str, float]
) -> pd.DataFrame:
    """
    Create a DataFrame in the exact feature order expected by the model.
    """

    return pd.DataFrame(
        [
            [
                data["semester"],
                data["cgpa"],
                data["attendance"],
                data["average_marks"],
                data["highest_marks"],
                data["lowest_marks"]
            ]
        ],
        columns=FEATURE_COLUMNS
    )


# ======================================================================
# RISK DESCRIPTION
# ======================================================================

def get_risk_description(
    risk_level: str
) -> str:
    """
    Return a human-readable description for the predicted risk.
    """

    descriptions = {

        "Low": (
            "The student is currently showing a healthy "
            "academic performance profile with relatively "
            "low predicted academic risk."
        ),

        "Moderate": (
            "The student shows some academic indicators "
            "that may require attention and monitoring."
        ),

        "High": (
            "The student shows a higher predicted academic "
            "risk and may require timely academic support."
        )
    }

    return descriptions.get(
        risk_level,
        "Academic risk could not be determined."
    )


# ======================================================================
# RECOMMENDATIONS
# ======================================================================

def generate_recommendations(
    data: Dict[str, float],
    risk_level: str
) -> list[str]:
    """
    Generate recommendations using the same actual academic
    variables supplied to the model.

    No assignment/internal/study-hour fields are referenced.
    """

    recommendations = []


    # --------------------------------------------------------------
    # Risk-level recommendation
    # --------------------------------------------------------------

    if risk_level == "Low":

        recommendations.append(
            "Academic performance is currently on a healthy track."
        )

    elif risk_level == "Moderate":

        recommendations.append(
            "Academic performance should be monitored regularly."
        )

    elif risk_level == "High":

        recommendations.append(
            "The student may benefit from timely academic intervention."
        )


    # --------------------------------------------------------------
    # CGPA
    # --------------------------------------------------------------

    cgpa = data["cgpa"]

    if cgpa < 6.0:

        recommendations.append(
            "Focus on improving overall academic performance "
            "to raise CGPA."
        )

    elif cgpa < 7.0:

        recommendations.append(
            "Consistent improvement in subject performance "
            "could help strengthen the CGPA."
        )


    # --------------------------------------------------------------
    # Attendance
    # --------------------------------------------------------------

    attendance = data["attendance"]

    if attendance < 75:

        recommendations.append(
            "Improve class attendance to support academic continuity."
        )

    elif attendance < 85:

        recommendations.append(
            "Maintaining higher attendance may further support "
            "academic performance."
        )


    # --------------------------------------------------------------
    # Average marks
    # --------------------------------------------------------------

    average_marks = data["average_marks"]

    if average_marks < 50:

        recommendations.append(
            "Additional academic support may be useful for "
            "improving average marks."
        )

    elif average_marks < 65:

        recommendations.append(
            "Focus on strengthening subject-wise performance "
            "to improve average marks."
        )


    # --------------------------------------------------------------
    # Performance consistency
    # --------------------------------------------------------------

    mark_range = (
        data["highest_marks"]
        -
        data["lowest_marks"]
    )

    if mark_range >= 30:

        recommendations.append(
            "There is a noticeable gap between highest and "
            "lowest marks; focus on weaker subjects for "
            "more consistent performance."
        )


    # --------------------------------------------------------------
    # Fallback
    # --------------------------------------------------------------

    if not recommendations:

        recommendations.append(
            "Continue maintaining consistent academic performance."
        )


    return recommendations


# ======================================================================
# PREDICT FROM FEATURES
# ======================================================================

def predict(
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform academic risk prediction.

    Parameters
    ----------
    data:
        Dictionary containing:

            semester
            cgpa
            attendance
            average_marks
            highest_marks
            lowest_marks

    Returns
    -------
    Dictionary containing:

        risk_level
        confidence
        probabilities
        recommendations
        description
        model
        features
    """

    # --------------------------------------------------------------
    # Validate input
    # --------------------------------------------------------------

    validated_data = validate_input(
        data
    )


    # --------------------------------------------------------------
    # Load artifact
    # --------------------------------------------------------------

    artifact = load_model()

    model = artifact[
        "model"
    ]

    label_encoder = artifact[
        "label_encoder"
    ]


    # --------------------------------------------------------------
    # Create model input
    # --------------------------------------------------------------

    X = create_feature_dataframe(
        validated_data
    )


    # --------------------------------------------------------------
    # Prediction
    # --------------------------------------------------------------

    prediction_encoded = (
        model
        .predict(X)
    )


    # --------------------------------------------------------------
    # Decode predicted class
    # --------------------------------------------------------------

    predicted_class = (
        label_encoder
        .inverse_transform(
            prediction_encoded.astype(int)
        )[0]
    )


    if predicted_class not in VALID_RISK_LEVELS:

        raise ValueError(
            f"Model returned unexpected risk level: "
            f"{predicted_class}"
        )


    # --------------------------------------------------------------
    # Probabilities
    # --------------------------------------------------------------

    probabilities = {}


    if hasattr(
        model,
        "predict_proba"
    ):

        probability_array = (
            model
            .predict_proba(X)[0]
        )

        model_classes = (
            label_encoder
            .classes_
        )

        for class_name, probability in zip(
            model_classes,
            probability_array
        ):

            probabilities[
                class_name
            ] = round(
                float(probability) * 100,
                2
            )


        confidence = round(
            max(
                probability_array
            ) * 100,
            2
        )

    else:

        confidence = None


    # --------------------------------------------------------------
    # Ensure all classes are present
    # --------------------------------------------------------------

    for class_name in [
        "High",
        "Low",
        "Moderate"
    ]:

        probabilities.setdefault(
            class_name,
            0.0
        )


    # --------------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------------

    recommendations = (
        generate_recommendations(
            validated_data,
            predicted_class
        )
    )


    # --------------------------------------------------------------
    # Model information
    # --------------------------------------------------------------

    metrics = (
        load_model_metrics()
    )

    model_name = (
        metrics.get(
            "best_model"
        )
        or artifact.get(
            "model_name"
        )
        or "Trained ML Model"
    )


    # --------------------------------------------------------------
    # Final response
    # --------------------------------------------------------------

    return {

        "success": True,

        "risk_level": predicted_class,

        "prediction": predicted_class,

        "confidence": confidence,

        "confidence_percentage": confidence,

        "probabilities": probabilities,

        "recommendations": recommendations,

        "description": (
            get_risk_description(
                predicted_class
            )
        ),

        "model": model_name,

        "model_version": (
            artifact.get(
                "model_version",
                "2.0"
            )
        ),

        "features": validated_data,

        "feature_names": FEATURE_COLUMNS
    }


# ======================================================================
# PREDICT FOR STUDENT OBJECT
# ======================================================================

def predict_student(
    student,
    average_marks: Optional[float] = None,
    highest_marks: Optional[float] = None,
    lowest_marks: Optional[float] = None,
    semester: Optional[int] = None
) -> Dict[str, Any]:
    """
    Predict risk for a Student database object.

    This helper is intended for Flask routes.

    Important:
    The Student object must provide:

        cgpa
        attendance

    Marks must be supplied from the student's actual Result records.

    Parameters
    ----------
    student:
        SQLAlchemy Student object.

    average_marks:
        Average marks calculated from actual Result records.

    highest_marks:
        Highest marks calculated from actual Result records.

    lowest_marks:
        Lowest marks calculated from actual Result records.

    semester:
        Current semester. If omitted, the function attempts to read
        student.semester.
    """

    # --------------------------------------------------------------
    # Semester
    # --------------------------------------------------------------

    if semester is None:

        semester = getattr(
            student,
            "semester",
            None
        )


    # --------------------------------------------------------------
    # Student academic fields
    # --------------------------------------------------------------

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


    # --------------------------------------------------------------
    # Validate database data
    # --------------------------------------------------------------

    if semester is None:

        raise ValueError(
            "Student semester is required for prediction."
        )

    if cgpa is None:

        raise ValueError(
            "Student CGPA is required for prediction."
        )

    if attendance is None:

        raise ValueError(
            "Student attendance is required for prediction."
        )

    if average_marks is None:

        raise ValueError(
            "Average marks are required for prediction."
        )

    if highest_marks is None:

        raise ValueError(
            "Highest marks are required for prediction."
        )

    if lowest_marks is None:

        raise ValueError(
            "Lowest marks are required for prediction."
        )


    # --------------------------------------------------------------
    # Run prediction
    # --------------------------------------------------------------

    return predict(
        {
            "semester": semester,
            "cgpa": cgpa,
            "attendance": attendance,
            "average_marks": average_marks,
            "highest_marks": highest_marks,
            "lowest_marks": lowest_marks
        }
    )


# ======================================================================
# HEALTH CHECK
# ======================================================================

def model_health_check() -> Dict[str, Any]:
    """
    Check whether the prediction model is available and correctly
    structured.
    """

    try:

        artifact = load_model()

        model = artifact.get(
            "model"
        )

        label_encoder = artifact.get(
            "label_encoder"
        )

        artifact_features = artifact.get(
            "feature_columns"
        )

        feature_match = (
            artifact_features
            == FEATURE_COLUMNS
        )

        return {

            "available": True,

            "model_loaded": model is not None,

            "label_encoder_loaded": (
                label_encoder is not None
            ),

            "features_valid": feature_match,

            "features": FEATURE_COLUMNS,

            "model_version": (
                artifact.get(
                    "model_version",
                    "unknown"
                )
            ),

            "trained_at": (
                artifact.get(
                    "trained_at"
                )
            )
        }

    except Exception as exc:

        return {

            "available": False,

            "model_loaded": False,

            "label_encoder_loaded": False,

            "features_valid": False,

            "features": FEATURE_COLUMNS,

            "error": str(exc)
        }


# ======================================================================
# TERMINAL TEST
# ======================================================================

def run_test():
    """
    Run a standalone prediction test.

    Execute from the project root:

        python services/prediction_service.py
    """

    print()
    print("=" * 70)
    print(
        "SMART STUDENT ANALYTICS SYSTEM"
    )
    print(
        "PREDICTION SERVICE TEST"
    )
    print("=" * 70)


    # --------------------------------------------------------------
    # Health check
    # --------------------------------------------------------------

    health = (
        model_health_check()
    )

    print()
    print("Model Health:")

    print(
        f"  Available       : "
        f"{health.get('available')}"
    )

    print(
        f"  Model Loaded    : "
        f"{health.get('model_loaded')}"
    )

    print(
        f"  Encoder Loaded  : "
        f"{health.get('label_encoder_loaded')}"
    )

    print(
        f"  Features Valid  : "
        f"{health.get('features_valid')}"
    )


    if not health.get(
        "available"
    ):

        print()
        print(
            "Prediction service test failed."
        )

        print(
            health.get(
                "error",
                "Unknown error"
            )
        )

        return


    # --------------------------------------------------------------
    # Test student data
    # --------------------------------------------------------------

    test_data = {

        "semester": 1,

        "cgpa": 7.85,

        "attendance": 66.67,

        "average_marks": 76.5,

        "highest_marks": 78.0,

        "lowest_marks": 75.0
    }


    # --------------------------------------------------------------
    # Run prediction
    # --------------------------------------------------------------

    try:

        result = predict(
            test_data
        )

    except Exception as exc:

        print()
        print(
            "Prediction failed:"
        )

        print(
            str(exc)
        )

        return


    # --------------------------------------------------------------
    # Display result
    # --------------------------------------------------------------

    print()
    print(
        "Input Features:"
    )

    for feature in FEATURE_COLUMNS:

        print(
            f"  {feature:<18}"
            f"{test_data[feature]}"
        )


    print()
    print(
        "Model:"
    )

    print(
        f"  {result['model']}"
    )


    print()
    print(
        "Predicted Risk:"
    )

    print(
        f"  {result['risk_level']}"
    )


    print()
    print(
        f"Confidence: "
        f"{result['confidence']:.2f}%"
    )


    print()
    print(
        "Probabilities:"
    )

    for label in [
        "High",
        "Low",
        "Moderate"
    ]:

        print(
            f"  {label:<10}"
            f"{result['probabilities'][label]:>6.2f}%"
        )


    print()
    print(
        "Recommendations:"
    )

    for recommendation in (
        result["recommendations"]
    ):

        print(
            f"  - {recommendation}"
        )


    print()
    print("=" * 70)
    print(
        "PREDICTION SERVICE TEST COMPLETED"
    )
    print("=" * 70)
    print()


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":

    run_test()
