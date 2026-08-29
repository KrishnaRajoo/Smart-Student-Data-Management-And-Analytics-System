"""
======================================================================
SMART STUDENT ANALYTICS SYSTEM
Student Academic Risk Prediction
ML Training Pipeline
======================================================================

Purpose
-------
Train and compare multiple machine-learning models for predicting
student academic risk.

IMPORTANT
---------
This training pipeline is intentionally compatible with the actual
SSAS academic feature structure.

MODEL INPUT FEATURES
--------------------
    1. semester
    2. cgpa
    3. attendance
    4. average_marks
    5. highest_marks
    6. lowest_marks

TARGET
------
    Low
    Moderate
    High

MODELS
------
    - Random Forest
    - Gradient Boosting
    - XGBoost

The model with the highest weighted F1 score is selected as the
production model.

OUTPUT
------
    ml/models/student_risk_model.pkl
    ml/models/model_metrics.json
    ml/models/model_features.json
======================================================================
"""

from __future__ import annotations

import json
import os
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier
)

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from sklearn.model_selection import train_test_split

from sklearn.preprocessing import LabelEncoder

from sklearn.pipeline import Pipeline

from sklearn.impute import SimpleImputer


# ======================================================================
# OPTIONAL XGBOOST IMPORT
# ======================================================================

try:
    from xgboost import XGBClassifier

    XGBOOST_AVAILABLE = True

except ImportError:
    XGBOOST_AVAILABLE = False


# ======================================================================
# CONFIGURATION
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR
    / "datasets"
    / "student_risk_dataset.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
)

MODEL_PATH = (
    MODEL_DIR
    / "student_risk_model.pkl"
)

METRICS_PATH = (
    MODEL_DIR
    / "model_metrics.json"
)

FEATURES_PATH = (
    MODEL_DIR
    / "model_features.json"
)


# ======================================================================
# REPRODUCIBILITY
# ======================================================================

RANDOM_STATE = 42

TEST_SIZE = 0.20


# ======================================================================
# FEATURES
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
# TARGET
# ======================================================================

TARGET_COLUMN = "target"


# ======================================================================
# CLASS LABELS
# ======================================================================

CLASS_LABELS = [
    "High",
    "Low",
    "Moderate"
]


# ======================================================================
# DISPLAY ORDER
# ======================================================================

DISPLAY_LABELS = [
    "Low",
    "Moderate",
    "High"
]


# ======================================================================
# WARNINGS
# ======================================================================

warnings.filterwarnings(
    "ignore"
)


# ======================================================================
# DIRECTORY SETUP
# ======================================================================

def create_directories():
    """
    Create the ML model directory if it does not exist.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# ======================================================================
# DATASET LOADING
# ======================================================================

def load_dataset():
    """
    Load the generated training dataset.
    """

    print()
    print("Loading dataset...")

    if not DATASET_PATH.exists():

        raise FileNotFoundError(
            f"\nDataset not found:\n{DATASET_PATH}\n\n"
            "Run the following command first:\n"
            "python ml/generate_dataset.py"
        )

    df = pd.read_csv(
        DATASET_PATH
    )

    print(
        f"Dataset loaded successfully: "
        f"{df.shape[0]} rows × {df.shape[1]} columns"
    )

    return df


# ======================================================================
# DATASET VALIDATION
# ======================================================================

def validate_dataset(df):
    """
    Validate the training dataset.

    Only the expected six features and target are accepted.
    """

    print()
    print("Validating dataset...")

    expected_columns = (
        FEATURE_COLUMNS
        + [TARGET_COLUMN]
    )

    actual_columns = list(
        df.columns
    )

    # --------------------------------------------------------------
    # Missing columns
    # --------------------------------------------------------------

    missing_columns = [
        column
        for column in expected_columns
        if column not in actual_columns
    ]

    if missing_columns:

        raise ValueError(
            "Missing required columns:\n"
            f"{missing_columns}"
        )


    # --------------------------------------------------------------
    # Unexpected columns
    # --------------------------------------------------------------

    unexpected_columns = [
        column
        for column in actual_columns
        if column not in expected_columns
    ]

    if unexpected_columns:

        raise ValueError(
            "Unexpected columns found in dataset:\n"
            f"{unexpected_columns}\n\n"
            "The training dataset must contain ONLY:\n"
            f"{expected_columns}"
        )


    # --------------------------------------------------------------
    # Missing values
    # --------------------------------------------------------------

    missing_values = (
        df[
            expected_columns
        ]
        .isnull()
        .sum()
    )

    if missing_values.sum() > 0:

        print()
        print("Missing values detected:")

        print(
            missing_values[
                missing_values > 0
            ]
        )

        raise ValueError(
            "Dataset contains missing values."
        )


    # --------------------------------------------------------------
    # Target validation
    # --------------------------------------------------------------

    valid_targets = {
        "Low",
        "Moderate",
        "High"
    }

    actual_targets = set(
        df[TARGET_COLUMN]
        .unique()
    )

    invalid_targets = (
        actual_targets
        - valid_targets
    )

    if invalid_targets:

        raise ValueError(
            "Invalid target labels found:\n"
            f"{invalid_targets}\n\n"
            "Expected labels:\n"
            f"{valid_targets}"
        )


    # --------------------------------------------------------------
    # Numeric validation
    # --------------------------------------------------------------

    for column in FEATURE_COLUMNS:

        if not pd.api.types.is_numeric_dtype(
            df[column]
        ):

            raise ValueError(
                f"Feature '{column}' must be numeric."
            )


    # --------------------------------------------------------------
    # Range checks
    # --------------------------------------------------------------

    if not df["semester"].between(
        1,
        8
    ).all():

        raise ValueError(
            "Semester values must be between 1 and 8."
        )


    if not df["cgpa"].between(
        4.0,
        10.0
    ).all():

        raise ValueError(
            "CGPA values must be between 4.0 and 10.0."
        )


    if not df["attendance"].between(
        0.0,
        100.0
    ).all():

        raise ValueError(
            "Attendance values must be between 0 and 100."
        )


    if not df["average_marks"].between(
        0.0,
        100.0
    ).all():

        raise ValueError(
            "Average marks must be between 0 and 100."
        )


    if not df["highest_marks"].between(
        0.0,
        100.0
    ).all():

        raise ValueError(
            "Highest marks must be between 0 and 100."
        )


    if not df["lowest_marks"].between(
        0.0,
        100.0
    ).all():

        raise ValueError(
            "Lowest marks must be between 0 and 100."
        )


    # --------------------------------------------------------------
    # Logical academic relationships
    # --------------------------------------------------------------

    if not (
        df["highest_marks"]
        >=
        df["average_marks"]
    ).all():

        raise ValueError(
            "highest_marks cannot be lower than average_marks."
        )


    if not (
        df["lowest_marks"]
        <=
        df["average_marks"]
    ).all():

        raise ValueError(
            "lowest_marks cannot be greater than average_marks."
        )


    print(
        "Dataset validation successful."
    )


# ======================================================================
# TARGET DISTRIBUTION
# ======================================================================

def print_target_distribution(df):
    """
    Display target class distribution.
    """

    print()
    print("Target distribution:")

    counts = (
        df[TARGET_COLUMN]
        .value_counts()
        .reindex(
            DISPLAY_LABELS,
            fill_value=0
        )
    )

    for label, count in counts.items():

        percentage = (
            count / len(df)
        ) * 100

        print(
            f"  {label:<10}"
            f"{count:>6}"
            f" ({percentage:>6.2f}%)"
        )


# ======================================================================
# TARGET ENCODING
# ======================================================================

def encode_target(y):
    """
    Encode string target labels into numeric labels.

    XGBoost requires numeric class labels.

    Example:

        0 -> High
        1 -> Low
        2 -> Moderate
    """

    label_encoder = LabelEncoder()

    y_encoded = (
        label_encoder
        .fit_transform(y)
    )

    print()
    print("Target label encoding:")

    for numeric_label, class_name in enumerate(
        label_encoder.classes_
    ):

        print(
            f"  {numeric_label} -> {class_name}"
        )

    return (
        y_encoded,
        label_encoder
    )


# ======================================================================
# PREPROCESSING
# ======================================================================

def create_preprocessor():
    """
    Create a simple preprocessing pipeline.

    Numeric missing values are handled defensively even though the
    current dataset validation rejects missing values.
    """

    return Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            )
        ]
    )


# ======================================================================
# MODEL CREATION
# ======================================================================

def create_random_forest():
    """
    Create Random Forest classifier.
    """

    return RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )


def create_gradient_boosting():
    """
    Create Gradient Boosting classifier.
    """

    return GradientBoostingClassifier(
        n_estimators=250,
        learning_rate=0.05,
        max_depth=4,
        min_samples_split=4,
        min_samples_leaf=2,
        subsample=0.9,
        random_state=RANDOM_STATE
    )


def create_xgboost():
    """
    Create XGBoost classifier.

    The target is already LabelEncoded, therefore XGBoost receives
    numeric class labels 0, 1 and 2.
    """

    if not XGBOOST_AVAILABLE:

        return None

    return XGBClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        min_child_weight=2,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )


# ======================================================================
# METRIC CALCULATION
# ======================================================================

def calculate_metrics(
    y_true,
    y_pred
):
    """
    Calculate multiclass evaluation metrics.
    """

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1)
    }


# ======================================================================
# MODEL EVALUATION
# ======================================================================

def evaluate_model(
    model_name,
    pipeline,
    X_test,
    y_test,
    label_encoder
):
    """
    Evaluate a trained model and print detailed metrics.
    """

    y_pred = pipeline.predict(
        X_test
    )

    metrics = calculate_metrics(
        y_test,
        y_pred
    )

    # --------------------------------------------------------------
    # Decode labels for human-readable report
    # --------------------------------------------------------------

    y_test_labels = (
        label_encoder
        .inverse_transform(
            y_test
        )
    )

    y_pred_labels = (
        label_encoder
        .inverse_transform(
            y_pred.astype(int)
        )
    )

    print()
    print(model_name)
    print("-" * 50)

    print(
        f"Accuracy  : "
        f"{metrics['accuracy']:.4f}"
    )

    print(
        f"Precision : "
        f"{metrics['precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{metrics['recall']:.4f}"
    )

    print(
        f"F1 Score  : "
        f"{metrics['f1_score']:.4f}"
    )

    # --------------------------------------------------------------
    # Classification report
    # --------------------------------------------------------------

    print()
    print("Classification Report:")

    print(
        classification_report(
            y_test_labels,
            y_pred_labels,
            labels=DISPLAY_LABELS,
            zero_division=0
        )
    )

    # --------------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------------

    cm = confusion_matrix(
        y_test_labels,
        y_pred_labels,
        labels=DISPLAY_LABELS
    )

    print("Confusion Matrix:")

    print(cm)

    return metrics


# ======================================================================
# MODEL TRAINING
# ======================================================================

def train_models(
    X_train,
    X_test,
    y_train,
    y_test,
    label_encoder
):
    """
    Train all available models and select the best model based on
    weighted F1 score.
    """

    models = {
        "Random Forest": create_random_forest(),
        "Gradient Boosting": create_gradient_boosting()
    }


    # --------------------------------------------------------------
    # Add XGBoost when installed
    # --------------------------------------------------------------

    xgb_model = create_xgboost()

    if xgb_model is not None:

        models["XGBoost"] = xgb_model

        print()
        print(
            "XGBoost detected successfully."
        )

    else:

        print()
        print(
            "XGBoost not installed."
        )

        print(
            "Continuing with Random Forest "
            "and Gradient Boosting."
        )


    results = {}

    trained_models = {}


    # --------------------------------------------------------------
    # Train each model
    # --------------------------------------------------------------

    for model_name, model in models.items():

        print()
        print("=" * 70)
        print(
            f"Training: {model_name}"
        )
        print("=" * 70)


        # ----------------------------------------------------------
        # Preprocessing
        # ----------------------------------------------------------

        preprocessor = (
            create_preprocessor()
        )


        # ----------------------------------------------------------
        # Pipeline
        # ----------------------------------------------------------

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor
                ),
                (
                    "model",
                    model
                )
            ]
        )


        # ----------------------------------------------------------
        # Train
        # ----------------------------------------------------------

        pipeline.fit(
            X_train,
            y_train
        )


        # ----------------------------------------------------------
        # Evaluate
        # ----------------------------------------------------------

        metrics = evaluate_model(
            model_name=model_name,
            pipeline=pipeline,
            X_test=X_test,
            y_test=y_test,
            label_encoder=label_encoder
        )


        results[model_name] = metrics

        trained_models[model_name] = pipeline


    return (
        results,
        trained_models
    )


# ======================================================================
# MODEL COMPARISON
# ======================================================================

def print_model_comparison(results):
    """
    Print model comparison table.
    """

    print()
    print()
    print("=" * 80)
    print("MODEL COMPARISON")
    print("=" * 80)

    print(
        f"{'Model':<25}"
        f"{'Accuracy':>12}"
        f"{'Precision':>14}"
        f"{'Recall':>12}"
        f"{'F1 Score':>12}"
    )

    print("-" * 80)

    for model_name, metrics in results.items():

        print(
            f"{model_name:<25}"
            f"{metrics['accuracy']:>12.4f}"
            f"{metrics['precision']:>14.4f}"
            f"{metrics['recall']:>12.4f}"
            f"{metrics['f1_score']:>12.4f}"
        )

    print("=" * 80)


# ======================================================================
# BEST MODEL
# ======================================================================

def select_best_model(
    results,
    trained_models
):
    """
    Select the model with the highest weighted F1 score.

    F1 is preferred because the problem is multiclass academic-risk
    classification and the classes are not perfectly balanced.
    """

    best_model_name = max(
        results,
        key=lambda name:
            results[name]["f1_score"]
    )

    best_model = (
        trained_models[
            best_model_name
        ]
    )

    return (
        best_model_name,
        best_model
    )


# ======================================================================
# FEATURE IMPORTANCE
# ======================================================================

def extract_feature_importance(
    model
):
    """
    Extract feature importance when supported by the selected model.
    """

    try:

        estimator = (
            model
            .named_steps["model"]
        )

        if not hasattr(
            estimator,
            "feature_importances_"
        ):

            return None

        importances = (
            estimator
            .feature_importances_
        )

        feature_importance = {}

        for feature, importance in zip(
            FEATURE_COLUMNS,
            importances
        ):

            feature_importance[
                feature
            ] = float(importance)

        return feature_importance

    except Exception:

        return None


# ======================================================================
# SAVE MODEL
# ======================================================================

def save_model(
    model,
    label_encoder
):
    """
    Save the trained production pipeline together with the label
    encoder.

    Keeping the label encoder inside the saved artifact ensures that
    prediction_service.py can correctly translate numeric predictions
    back into:

        High
        Low
        Moderate
    """

    model_artifact = {
        "model": model,
        "label_encoder": label_encoder,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "class_labels": list(
            label_encoder.classes_
        ),
        "model_version": "2.0",
        "trained_at": datetime.now().isoformat()
    }

    joblib.dump(
        model_artifact,
        MODEL_PATH
    )

    print()
    print("Model saved successfully:")
    print(MODEL_PATH)


# ======================================================================
# SAVE METRICS
# ======================================================================

def save_metrics(
    results,
    best_model_name
):
    """
    Save training and evaluation metrics as JSON.
    """

    best_metrics = (
        results[
            best_model_name
        ]
    )

    metrics_payload = {
        "project": (
            "Smart Student Analytics System"
        ),

        "task": (
            "Student Academic Risk Prediction"
        ),

        "model_selection_metric": (
            "weighted_f1"
        ),

        "best_model": best_model_name,

        "best_accuracy": (
            best_metrics["accuracy"]
        ),

        "best_precision": (
            best_metrics["precision"]
        ),

        "best_recall": (
            best_metrics["recall"]
        ),

        "best_f1_score": (
            best_metrics["f1_score"]
        ),

        "models": results,

        "features": FEATURE_COLUMNS,

        "target": TARGET_COLUMN,

        "target_classes": CLASS_LABELS,

        "training_dataset": str(
            DATASET_PATH
        ),

        "training_samples": 8000,

        "testing_samples": 2000,

        "trained_at": datetime.now().isoformat(),

        "random_state": RANDOM_STATE
    }

    with open(
        METRICS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metrics_payload,
            file,
            indent=4
        )

    print()
    print("Metrics saved:")
    print(METRICS_PATH)


# ======================================================================
# SAVE FEATURE METADATA
# ======================================================================

def save_feature_metadata(
    best_model_name,
    feature_importance=None
):
    """
    Save metadata describing the exact model input structure.
    """

    metadata = {
        "project": (
            "Smart Student Analytics System"
        ),

        "model_name": best_model_name,

        "model_version": "2.0",

        "feature_count": len(
            FEATURE_COLUMNS
        ),

        "features": [
            {
                "name": "semester",
                "type": "integer",
                "description": (
                    "Student academic semester"
                )
            },
            {
                "name": "cgpa",
                "type": "float",
                "description": (
                    "Student cumulative grade point average"
                )
            },
            {
                "name": "attendance",
                "type": "float",
                "description": (
                    "Student attendance percentage"
                )
            },
            {
                "name": "average_marks",
                "type": "float",
                "description": (
                    "Average academic marks"
                )
            },
            {
                "name": "highest_marks",
                "type": "float",
                "description": (
                    "Highest academic marks"
                )
            },
            {
                "name": "lowest_marks",
                "type": "float",
                "description": (
                    "Lowest academic marks"
                )
            }
        ],

        "target": {
            "name": TARGET_COLUMN,
            "classes": CLASS_LABELS,
            "description": (
                "Predicted academic risk category"
            )
        },

        "excluded_features": [
            "study_hours",
            "assignment_score",
            "internal_exam_score",
            "quiz_score",
            "project_score",
            "extracurricular_score"
        ],

        "training_dataset": str(
            DATASET_PATH
        ),

        "generated_at": datetime.now().isoformat()
    }


    if feature_importance is not None:

        metadata[
            "feature_importance"
        ] = feature_importance


    with open(
        FEATURES_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4
        )

    print()
    print("Feature metadata saved:")
    print(FEATURES_PATH)


# ======================================================================
# TRAINING PIPELINE
# ======================================================================

def train_model():
    """
    Main model-training pipeline.
    """

    print()
    print()
    print("=" * 70)
    print(
        "SMART STUDENT ANALYTICS SYSTEM"
    )
    print(
        "STUDENT ACADEMIC RISK PREDICTION"
    )
    print(
        "MODEL TRAINING PIPELINE"
    )
    print("=" * 70)


    # --------------------------------------------------------------
    # Create directories
    # --------------------------------------------------------------

    create_directories()


    # --------------------------------------------------------------
    # Load dataset
    # --------------------------------------------------------------

    df = load_dataset()


    # --------------------------------------------------------------
    # Validate dataset
    # --------------------------------------------------------------

    validate_dataset(
        df
    )


    # --------------------------------------------------------------
    # Display target distribution
    # --------------------------------------------------------------

    print_target_distribution(
        df
    )


    # --------------------------------------------------------------
    # Separate features and target
    # --------------------------------------------------------------

    X = df[
        FEATURE_COLUMNS
    ].copy()

    y = df[
        TARGET_COLUMN
    ].copy()


    # --------------------------------------------------------------
    # Encode target
    # --------------------------------------------------------------

    (
        y_encoded,
        label_encoder
    ) = encode_target(
        y
    )


    # --------------------------------------------------------------
    # Stratified train/test split
    # --------------------------------------------------------------

    print()
    print(
        "Creating stratified train/test split..."
    )

    (
        X_train,
        X_test,
        y_train,
        y_test
    ) = train_test_split(
        X,
        y_encoded,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y_encoded
    )


    print(
        f"Training samples : "
        f"{len(X_train)}"
    )

    print(
        f"Testing samples  : "
        f"{len(X_test)}"
    )


    # --------------------------------------------------------------
    # Train models
    # --------------------------------------------------------------

    (
        results,
        trained_models
    ) = train_models(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        label_encoder=label_encoder
    )


    # --------------------------------------------------------------
    # Model comparison
    # --------------------------------------------------------------

    print_model_comparison(
        results
    )


    # --------------------------------------------------------------
    # Select best model
    # --------------------------------------------------------------

    (
        best_model_name,
        best_model
    ) = select_best_model(
        results,
        trained_models
    )


    # --------------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------------

    feature_importance = (
        extract_feature_importance(
            best_model
        )
    )


    # --------------------------------------------------------------
    # Save production model
    # --------------------------------------------------------------

    save_model(
        model=best_model,
        label_encoder=label_encoder
    )


    # --------------------------------------------------------------
    # Save metrics
    # --------------------------------------------------------------

    save_metrics(
        results=results,
        best_model_name=best_model_name
    )


    # --------------------------------------------------------------
    # Save feature metadata
    # --------------------------------------------------------------

    save_feature_metadata(
        best_model_name=best_model_name,
        feature_importance=feature_importance
    )


    # ==================================================================
    # FINAL OUTPUT
    # ==================================================================

    best_metrics = (
        results[
            best_model_name
        ]
    )

    print()
    print()
    print("=" * 70)
    print(
        "TRAINING COMPLETED SUCCESSFULLY"
    )
    print("=" * 70)

    print()
    print(
        f"Best Model: "
        f"{best_model_name}"
    )

    print(
        f"Best Weighted F1: "
        f"{best_metrics['f1_score']:.4f}"
    )

    print(
        f"Best Accuracy: "
        f"{best_metrics['accuracy']:.4f}"
    )

    print()
    print("Model features:")

    for feature in FEATURE_COLUMNS:

        print(
            f"  ✓ {feature}"
        )

    print()
    print("Generated model files:")

    print(
        f"  1. {MODEL_PATH}"
    )

    print(
        f"  2. {METRICS_PATH}"
    )

    print(
        f"  3. {FEATURES_PATH}"
    )

    print()
    print(
        "The trained prediction pipeline is "
        "ready for integration."
    )

    print("=" * 70)
    print()


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":

    train_model()
