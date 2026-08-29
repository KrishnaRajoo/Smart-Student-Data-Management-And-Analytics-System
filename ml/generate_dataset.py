"""
======================================================================
SMART STUDENT ANALYTICS SYSTEM
Synthetic Academic Risk Dataset Generator
======================================================================

Purpose
-------
Generate a synthetic dataset ONLY for training the academic risk
prediction model.

IMPORTANT
---------
The generated features are intentionally restricted to the fields that
are compatible with the actual SSAS academic data:

    1. semester
    2. cgpa
    3. attendance
    4. average_marks
    5. highest_marks
    6. lowest_marks

Target:

    Low
    Moderate
    High

This script does NOT generate:
    - study_hours
    - assignment_score
    - internal_exam_score
    - quiz_score
    - project_score
    - extracurricular_score
    - any other fabricated academic field

The synthetic dataset is for MODEL TRAINING ONLY.

The deployed prediction system should ultimately obtain prediction
features from the actual SSAS database.
======================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================================
# CONFIGURATION
# ======================================================================

RANDOM_SEED = 42
NUM_SAMPLES = 10000

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "datasets"
DATASET_PATH = DATASET_DIR / "student_risk_dataset.csv"


# ======================================================================
# RANDOM GENERATOR
# ======================================================================

rng = np.random.default_rng(RANDOM_SEED)


# ======================================================================
# HELPER FUNCTIONS
# ======================================================================

def clip(value, minimum, maximum):
    """
    Restrict a value to a specified range.
    """
    return np.clip(value, minimum, maximum)


def generate_cgpa():
    """
    Generate realistic CGPA values approximately within the
    4.0 - 10.0 range.
    """

    # Most students are centered around the middle-to-upper range.
    cgpa = rng.normal(loc=7.7, scale=1.25, size=NUM_SAMPLES)

    return np.round(
        clip(cgpa, 4.0, 10.0),
        2
    )


def generate_attendance(cgpa):
    """
    Generate attendance percentages.

    Attendance has a weak positive relationship with CGPA, while still
    retaining substantial natural variation.
    """

    attendance = (
        82
        + (cgpa - 7.5) * 4.0
        + rng.normal(0, 13, NUM_SAMPLES)
    )

    # Include realistic lower and upper boundaries.
    attendance = clip(
        attendance,
        50.0,
        100.0
    )

    return np.round(attendance, 2)


def generate_average_marks(cgpa, attendance):
    """
    Generate average subject marks.

    Marks are influenced by CGPA and attendance, with random variation.
    """

    average_marks = (
        55
        + (cgpa - 5.0) * 7.2
        + (attendance - 70.0) * 0.22
        + rng.normal(0, 7.5, NUM_SAMPLES)
    )

    average_marks = clip(
        average_marks,
        35.0,
        98.0
    )

    return np.round(
        average_marks,
        2
    )


def generate_highest_marks(average_marks):
    """
    Generate highest marks.

    Highest marks should normally be greater than or equal to the
    average marks.
    """

    highest_marks = (
        average_marks
        + np.abs(
            rng.normal(
                loc=8.0,
                scale=4.0,
                size=NUM_SAMPLES
            )
        )
    )

    highest_marks = clip(
        highest_marks,
        40.0,
        100.0
    )

    # Ensure highest >= average.
    highest_marks = np.maximum(
        highest_marks,
        average_marks
    )

    return np.round(
        highest_marks,
        2
    )


def generate_lowest_marks(average_marks):
    """
    Generate lowest marks.

    Lowest marks should normally be less than or equal to the
    average marks.
    """

    lowest_marks = (
        average_marks
        - np.abs(
            rng.normal(
                loc=9.0,
                scale=4.0,
                size=NUM_SAMPLES
            )
        )
    )

    lowest_marks = clip(
        lowest_marks,
        25.0,
        95.0
    )

    # Ensure lowest <= average.
    lowest_marks = np.minimum(
        lowest_marks,
        average_marks
    )

    return np.round(
        lowest_marks,
        2
    )


def generate_semester():
    """
    Generate semester values.

    SSAS currently uses semester information as an academic feature.
    """

    semesters = rng.integers(
        low=1,
        high=9,
        size=NUM_SAMPLES
    )

    return semesters.astype(int)


# ======================================================================
# RISK GENERATION
# ======================================================================

def calculate_academic_risk_score(
    cgpa,
    attendance,
    average_marks,
    highest_marks,
    lowest_marks,
    semester
):
    """
    Calculate a continuous academic-risk score.

    Higher score = greater academic risk.

    The score is generated from the same type of information available
    in the SSAS academic system.

    NOTE:
    This score is used only to construct a realistic synthetic target
    for model training.
    """

    # --------------------------------------------------------------
    # CGPA risk
    # --------------------------------------------------------------

    cgpa_risk = (
        10.0 - cgpa
    ) / 6.0

    cgpa_risk = clip(
        cgpa_risk,
        0.0,
        1.0
    )


    # --------------------------------------------------------------
    # Attendance risk
    # --------------------------------------------------------------

    attendance_risk = (
        100.0 - attendance
    ) / 50.0

    attendance_risk = clip(
        attendance_risk,
        0.0,
        1.0
    )


    # --------------------------------------------------------------
    # Average marks risk
    # --------------------------------------------------------------

    marks_risk = (
        100.0 - average_marks
    ) / 65.0

    marks_risk = clip(
        marks_risk,
        0.0,
        1.0
    )


    # --------------------------------------------------------------
    # Lowest marks risk
    # --------------------------------------------------------------

    lowest_marks_risk = (
        100.0 - lowest_marks
    ) / 75.0

    lowest_marks_risk = clip(
        lowest_marks_risk,
        0.0,
        1.0
    )


    # --------------------------------------------------------------
    # Performance consistency
    # --------------------------------------------------------------

    marks_spread = (
        highest_marks - lowest_marks
    )

    consistency_risk = (
        marks_spread / 60.0
    )

    consistency_risk = clip(
        consistency_risk,
        0.0,
        1.0
    )


    # --------------------------------------------------------------
    # Semester factor
    # --------------------------------------------------------------
    #
    # Semester has intentionally low influence.
    #
    # We do NOT want the model to learn:
    #
    # "higher semester = higher risk"
    #
    # because that would be an unrealistic shortcut.
    # --------------------------------------------------------------

    semester_factor = (
        np.abs(semester - 4.5) / 4.5
    )

    semester_factor = clip(
        semester_factor,
        0.0,
        1.0
    )


    # --------------------------------------------------------------
    # Combined academic risk
    # --------------------------------------------------------------

    risk_score = (
        0.34 * cgpa_risk
        + 0.22 * attendance_risk
        + 0.28 * marks_risk
        + 0.10 * lowest_marks_risk
        + 0.04 * consistency_risk
        + 0.02 * semester_factor
    )


    # --------------------------------------------------------------
    # Add small natural variation
    # --------------------------------------------------------------

    risk_score += rng.normal(
        loc=0.0,
        scale=0.035,
        size=NUM_SAMPLES
    )

    return risk_score


def convert_score_to_target(risk_score):
    """
    Convert continuous risk scores into three academic-risk classes.

    Classes:

        Low
        Moderate
        High

    The thresholds are intentionally chosen to produce a dataset with
    enough examples in each class for multiclass model training.
    """

    target = np.select(
        [
            risk_score < 0.34,
            risk_score < 0.52
        ],
        [
            "Low",
            "Moderate"
        ],
        default="High"
    )

    return target


# ======================================================================
# DATASET VALIDATION
# ======================================================================

def validate_dataset(df):
    """
    Validate generated dataset before saving it.
    """

    print()
    print("=" * 70)
    print("DATASET VALIDATION")
    print("=" * 70)

    required_columns = [
        "semester",
        "cgpa",
        "attendance",
        "average_marks",
        "highest_marks",
        "lowest_marks",
        "target"
    ]

    # --------------------------------------------------------------
    # Column validation
    # --------------------------------------------------------------

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    unexpected_columns = [
        column
        for column in df.columns
        if column not in required_columns
    ]

    if unexpected_columns:
        raise ValueError(
            f"Unexpected columns detected: {unexpected_columns}"
        )


    # --------------------------------------------------------------
    # Row validation
    # --------------------------------------------------------------

    if len(df) != NUM_SAMPLES:
        raise ValueError(
            f"Expected {NUM_SAMPLES} rows, "
            f"but generated {len(df)} rows."
        )


    # --------------------------------------------------------------
    # Missing values
    # --------------------------------------------------------------

    if df.isnull().sum().sum() > 0:
        raise ValueError(
            "Dataset contains missing values."
        )


    # --------------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------------

    duplicate_count = df.duplicated().sum()

    if duplicate_count > 0:
        print(
            f"Warning: {duplicate_count} duplicate rows detected."
        )


    # --------------------------------------------------------------
    # Range validation
    # --------------------------------------------------------------

    if not df["semester"].between(1, 8).all():
        raise ValueError(
            "Invalid semester value detected."
        )

    if not df["cgpa"].between(4.0, 10.0).all():
        raise ValueError(
            "Invalid CGPA value detected."
        )

    if not df["attendance"].between(50.0, 100.0).all():
        raise ValueError(
            "Invalid attendance value detected."
        )

    if not df["average_marks"].between(35.0, 98.0).all():
        raise ValueError(
            "Invalid average_marks value detected."
        )

    if not df["highest_marks"].between(40.0, 100.0).all():
        raise ValueError(
            "Invalid highest_marks value detected."
        )

    if not df["lowest_marks"].between(25.0, 95.0).all():
        raise ValueError(
            "Invalid lowest_marks value detected."
        )


    # --------------------------------------------------------------
    # Logical academic relationships
    # --------------------------------------------------------------

    if not (
        df["highest_marks"] >= df["average_marks"]
    ).all():
        raise ValueError(
            "highest_marks cannot be lower than average_marks."
        )

    if not (
        df["lowest_marks"] <= df["average_marks"]
    ).all():
        raise ValueError(
            "lowest_marks cannot be greater than average_marks."
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
        df["target"].unique()
    )

    invalid_targets = (
        actual_targets - valid_targets
    )

    if invalid_targets:
        raise ValueError(
            f"Invalid target labels: {invalid_targets}"
        )


    print("✓ Required columns validated")
    print("✓ Row count validated")
    print("✓ Missing values validated")
    print("✓ Feature ranges validated")
    print("✓ Academic relationships validated")
    print("✓ Target labels validated")
    print()
    print("Dataset validation successful.")


# ======================================================================
# DATASET GENERATION
# ======================================================================

def generate_dataset():
    """
    Generate the complete synthetic academic risk dataset.
    """

    print("=" * 70)
    print("SMART STUDENT ANALYTICS SYSTEM")
    print("SYNTHETIC ACADEMIC RISK DATASET GENERATOR")
    print("=" * 70)

    print()
    print(f"Random seed : {RANDOM_SEED}")
    print(f"Samples     : {NUM_SAMPLES}")

    print()
    print("Generating SSAS-compatible academic features...")


    # --------------------------------------------------------------
    # Generate base features
    # --------------------------------------------------------------

    semester = generate_semester()

    cgpa = generate_cgpa()

    attendance = generate_attendance(
        cgpa
    )

    average_marks = generate_average_marks(
        cgpa,
        attendance
    )

    highest_marks = generate_highest_marks(
        average_marks
    )

    lowest_marks = generate_lowest_marks(
        average_marks
    )


    # --------------------------------------------------------------
    # Generate synthetic target
    # --------------------------------------------------------------

    risk_score = calculate_academic_risk_score(
        cgpa=cgpa,
        attendance=attendance,
        average_marks=average_marks,
        highest_marks=highest_marks,
        lowest_marks=lowest_marks,
        semester=semester
    )

    target = convert_score_to_target(
        risk_score
    )


    # --------------------------------------------------------------
    # Construct final dataframe
    # --------------------------------------------------------------

    df = pd.DataFrame(
        {
            "semester": semester,
            "cgpa": cgpa,
            "attendance": attendance,
            "average_marks": average_marks,
            "highest_marks": highest_marks,
            "lowest_marks": lowest_marks,
            "target": target
        }
    )


    # --------------------------------------------------------------
    # Shuffle dataset
    # --------------------------------------------------------------

    df = df.sample(
        frac=1.0,
        random_state=RANDOM_SEED
    ).reset_index(
        drop=True
    )


    # --------------------------------------------------------------
    # Validate
    # --------------------------------------------------------------

    validate_dataset(
        df
    )


    # --------------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------------

    DATASET_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------------------
    # Save CSV
    # --------------------------------------------------------------

    df.to_csv(
        DATASET_PATH,
        index=False
    )


    # ==================================================================
    # DISPLAY INFORMATION
    # ==================================================================

    print()
    print("=" * 70)
    print("DATASET GENERATED SUCCESSFULLY")
    print("=" * 70)

    print()
    print(f"Output file:")
    print(DATASET_PATH)

    print()
    print(f"Dataset shape:")
    print(
        f"{df.shape[0]} rows × {df.shape[1]} columns"
    )

    print()
    print("Columns:")
    for index, column in enumerate(
        df.columns,
        start=1
    ):
        print(
            f"  {index}. {column}"
        )


    # --------------------------------------------------------------
    # Target distribution
    # --------------------------------------------------------------

    print()
    print("Target distribution:")

    target_counts = (
        df["target"]
        .value_counts()
        .reindex(
            ["Low", "Moderate", "High"],
            fill_value=0
        )
    )

    for label, count in target_counts.items():

        percentage = (
            count / len(df)
        ) * 100

        print(
            f"  {label:<10} "
            f"{count:>5} "
            f"({percentage:>6.2f}%)"
        )


    # --------------------------------------------------------------
    # Dataset preview
    # --------------------------------------------------------------

    print()
    print("Dataset preview:")
    print(
        df.head(10).to_string(
            index=False
        )
    )


    # --------------------------------------------------------------
    # Statistical summary
    # --------------------------------------------------------------

    print()
    print("Feature summary:")

    print(
        df[
            [
                "semester",
                "cgpa",
                "attendance",
                "average_marks",
                "highest_marks",
                "lowest_marks"
            ]
        ].describe().round(2).to_string()
    )


    # --------------------------------------------------------------
    # Explicit feature confirmation
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("MODEL FEATURES")
    print("=" * 70)

    print()
    print(
        "The following features will be available to the model:"
    )

    model_features = [
        "semester",
        "cgpa",
        "attendance",
        "average_marks",
        "highest_marks",
        "lowest_marks"
    ]

    for feature in model_features:
        print(
            f"  ✓ {feature}"
        )

    print()
    print(
        "No assignment, internal-exam, study-hour, "
        "quiz, or fabricated features were generated."
    )


    print()
    print("=" * 70)
    print("GENERATION COMPLETED")
    print("=" * 70)

    print()
    print(
        "This dataset is intended for ML model training only."
    )

    print(
        "Production predictions should use actual "
        "SSAS database information."
    )

    print()


# ======================================================================
# MAIN
# ======================================================================

if __name__ == "__main__":
    generate_dataset()
