"""Week 3: baseline cancellation prediction models."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".matplotlib-cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

sys.path.append(str(Path(__file__).resolve().parent))
from clean_data import clean_and_engineer, load_dataset  # noqa: E402
from config import (  # noqa: E402
    CLEANED_DATA_PATH,
    MODEL_FEATURE_IMPORTANCE_PATH,
    MODEL_METRICS_PATH,
    MODELING_REPORT_PATH,
    VISUALIZATIONS_DIR,
    ensure_directories,
)


sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.figsize"] = (11, 7)
plt.rcParams["savefig.dpi"] = 160
plt.rcParams["font.family"] = "DejaVu Sans"

TARGET = "is_canceled"
RANDOM_STATE = 42

NUMERIC_FEATURES = [
    "lead_time",
    "arrival_date_year",
    "arrival_month_number",
    "arrival_date_week_number",
    "arrival_date_day_of_month",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
    "adults",
    "children",
    "babies",
    "is_repeated_guest",
    "previous_cancellations",
    "previous_bookings_not_canceled",
    "booking_changes",
    "agent",
    "company",
    "days_in_waiting_list",
    "adr",
    "required_car_parking_spaces",
    "total_of_special_requests",
    "total_stay",
    "total_guests",
    "booking_value",
    "adr_per_guest",
    "has_agent",
    "has_company",
    "has_special_requests",
    "is_family_booking",
    "is_weekend_stay",
    "is_long_stay",
]

CATEGORICAL_FEATURES = [
    "hotel",
    "arrival_date_month",
    "meal",
    "country",
    "market_segment",
    "distribution_channel",
    "reserved_room_type",
    "deposit_type",
    "customer_type",
    "booking_season",
    "lead_time_bucket",
    "stay_length_bucket",
    "traveller_segment",
    "customer_value_segment",
]


def load_modeling_data() -> pd.DataFrame:
    """Load the cleaned dataset, creating it from the approved raw file if needed."""
    if CLEANED_DATA_PATH.exists():
        return pd.read_csv(CLEANED_DATA_PATH)

    raw = load_dataset()
    cleaned, _ = clean_and_engineer(raw)
    cleaned.to_csv(CLEANED_DATA_PATH, index=False)
    return cleaned


def build_preprocessor() -> ColumnTransformer:
    """Build preprocessing for numeric and categorical model inputs."""
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def build_models() -> dict[str, Pipeline]:
    """Create baseline classification models."""
    return {
        "Logistic Regression": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        solver="lbfgs",
                    ),
                ),
            ]
        ),
        "Decision Tree": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "model",
                    DecisionTreeClassifier(
                        max_depth=7,
                        min_samples_leaf=100,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def evaluate_model(
    model_name: str,
    pipeline: Pipeline,
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> dict[str, Any]:
    """Train and evaluate one model."""
    pipeline.fit(x_train, y_train)
    y_pred = pipeline.predict(x_test)
    y_probability = pipeline.predict_proba(x_test)[:, 1]

    return {
        "model": model_name,
        "pipeline": pipeline,
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_probability),
        "confusion_matrix": confusion_matrix(y_test, y_pred),
        "classification_report": classification_report(
            y_test,
            y_pred,
            target_names=["Not canceled", "Canceled"],
            zero_division=0,
        ),
        "y_probability": y_probability,
        "y_pred": y_pred,
    }


def save_roc_curve(results: list[dict[str, Any]], y_test: pd.Series) -> str:
    """Save ROC curve comparison for all models."""
    plt.figure(figsize=(10, 7))
    for result in results:
        fpr, tpr, _ = roc_curve(y_test, result["y_probability"])
        plt.plot(fpr, tpr, linewidth=2, label=f"{result['model']} AUC={result['roc_auc']:.3f}")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random baseline")
    plt.title("Week 3 ROC Curve - Cancellation Prediction")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend(loc="lower right")
    path = VISUALIZATIONS_DIR / "22_week3_roc_curve.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return str(path)


def save_confusion_matrix(result: dict[str, Any]) -> str:
    """Save confusion matrix plot for one model."""
    display = ConfusionMatrixDisplay(
        confusion_matrix=result["confusion_matrix"],
        display_labels=["Not canceled", "Canceled"],
    )
    display.plot(cmap="Blues", values_format="d")
    plt.title(f"Week 3 Confusion Matrix - {result['model']}")
    path = VISUALIZATIONS_DIR / f"23_week3_confusion_matrix_{result['model'].lower().replace(' ', '_')}.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return str(path)


def feature_importance_table(best_result: dict[str, Any]) -> pd.DataFrame:
    """Create feature importance table for the selected best model."""
    pipeline = best_result["pipeline"]
    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]
    feature_names = preprocessor.get_feature_names_out()

    if hasattr(model, "coef_"):
        importance = np.abs(model.coef_[0])
        signed_effect = model.coef_[0]
    else:
        importance = model.feature_importances_
        signed_effect = model.feature_importances_

    table = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importance,
            "signed_effect": signed_effect,
        }
    )
    table["feature"] = (
        table["feature"]
        .str.replace("numeric__", "", regex=False)
        .str.replace("categorical__", "", regex=False)
    )
    return table.sort_values("importance", ascending=False).head(25).reset_index(drop=True)


def save_feature_importance_plot(feature_importance: pd.DataFrame, model_name: str) -> str:
    """Save top feature importance chart."""
    top_features = feature_importance.head(15).sort_values("importance")
    plt.figure(figsize=(11, 8))
    sns.barplot(data=top_features, x="importance", y="feature", color="#4C78A8")
    plt.title(f"Top Cancellation Prediction Features - {model_name}")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    path = VISUALIZATIONS_DIR / "24_week3_feature_importance.png"
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return str(path)


def markdown_table(df: pd.DataFrame, floatfmt: str = ".3f") -> str:
    """Render a compact Markdown table without optional dependencies."""
    formatted = df.copy()
    for column in formatted.columns:
        if pd.api.types.is_float_dtype(formatted[column]):
            formatted[column] = formatted[column].map(lambda value: format(value, floatfmt))
    formatted = formatted.astype(str)
    columns = list(formatted.columns)
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = [
        "| " + " | ".join(row[column] for column in columns) + " |"
        for _, row in formatted.iterrows()
    ]
    return "\n".join([header, separator, *rows])


def write_modeling_report(
    metrics: pd.DataFrame,
    results: list[dict[str, Any]],
    best_result: dict[str, Any],
    feature_importance: pd.DataFrame,
    roc_path: str,
    confusion_paths: list[str],
    train_rows: int,
    test_rows: int,
    cancellation_rate: float,
) -> None:
    """Write Week 3 modeling report."""
    report_paths = "\n".join(f"- `{Path(path).relative_to(MODELING_REPORT_PATH.parents[1])}`" for path in confusion_paths)
    classification_blocks = "\n\n".join(
        f"""### {result["model"]} Classification Report

```text
{result["classification_report"]}
```"""
        for result in results
    )

    MODELING_REPORT_PATH.write_text(
        f"""# Week 3 Predictive Modeling Report

## Objective

Build baseline machine learning models to predict whether a booking will be canceled. This supports customer retention campaigns, cancellation-risk scoring, and cancellation-adjusted revenue forecasting.

## Data Setup

- Target variable: `is_canceled`
- Training rows: {train_rows:,}
- Testing rows: {test_rows:,}
- Overall cancellation rate: {cancellation_rate:.2%}
- Split method: stratified 80/20 train-test split
- Models trained: Logistic Regression and Decision Tree

## Leakage Controls

The model excludes `reservation_status`, `reservation_status_date`, `assigned_room_type`, and `room_type_changed` because they can represent post-booking or outcome-adjacent information. The retained features are known or reasonably available at booking time.

## Model Performance

{markdown_table(metrics[["model", "accuracy", "precision", "recall", "roc_auc"]])}

Best baseline model by ROC-AUC: **{best_result["model"]}**

![ROC Curve](../visualizations/22_week3_roc_curve.png)

## Confusion Matrices

{report_paths}

## Top Predictive Features

![Feature Importance](../visualizations/24_week3_feature_importance.png)

{markdown_table(feature_importance.head(15))}

{classification_blocks}

## Business Interpretation

- High recall helps identify more bookings likely to cancel, which is useful for retention campaigns.
- Precision shows how many flagged bookings are truly cancellations, which matters for avoiding unnecessary discounts.
- ROC-AUC is the best comparison metric here because it evaluates ranking quality across thresholds.
- The baseline model is suitable for decision support, not yet for automated production pricing.

## Recommendations for Week 4 and Future Work

- Use predicted cancellation probability in expected revenue: `expected_revenue = booking_value * (1 - cancellation_probability)`.
- Create risk bands such as low, medium, and high cancellation probability.
- Target high-risk, high-value bookings with retention offers before arrival.
- Tune classification thresholds by business cost, not only by default model cutoff.
- Add cross-validation and hyperparameter tuning before production deployment.
""",
        encoding="utf-8",
    )


def run_modeling() -> None:
    """Run Week 3 predictive modeling workflow."""
    ensure_directories()
    df = load_modeling_data()

    available_numeric = [column for column in NUMERIC_FEATURES if column in df.columns]
    available_categorical = [column for column in CATEGORICAL_FEATURES if column in df.columns]
    model_df = df[[TARGET, *available_numeric, *available_categorical]].copy()

    x = model_df.drop(columns=[TARGET])
    y = model_df[TARGET].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    results = [
        evaluate_model(name, pipeline, x_train, x_test, y_train, y_test)
        for name, pipeline in build_models().items()
    ]

    metrics = pd.DataFrame(
        [
            {
                "model": result["model"],
                "accuracy": result["accuracy"],
                "precision": result["precision"],
                "recall": result["recall"],
                "roc_auc": result["roc_auc"],
            }
            for result in results
        ]
    ).sort_values("roc_auc", ascending=False)

    best_result = max(results, key=lambda result: result["roc_auc"])
    feature_importance = feature_importance_table(best_result)

    metrics.to_csv(MODEL_METRICS_PATH, index=False)
    feature_importance.to_csv(MODEL_FEATURE_IMPORTANCE_PATH, index=False)

    roc_path = save_roc_curve(results, y_test)
    confusion_paths = [save_confusion_matrix(result) for result in results]
    save_feature_importance_plot(feature_importance, best_result["model"])

    write_modeling_report(
        metrics=metrics,
        results=results,
        best_result=best_result,
        feature_importance=feature_importance,
        roc_path=roc_path,
        confusion_paths=confusion_paths,
        train_rows=len(x_train),
        test_rows=len(x_test),
        cancellation_rate=float(y.mean()),
    )

    print(f"Model metrics saved to: {MODEL_METRICS_PATH}")
    print(f"Feature importance saved to: {MODEL_FEATURE_IMPORTANCE_PATH}")
    print(f"Modeling report saved to: {MODELING_REPORT_PATH}")
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    run_modeling()
