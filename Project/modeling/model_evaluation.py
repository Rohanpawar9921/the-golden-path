"""Small, dependency-light evaluation functions used by training jobs."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


def _roc_auc(model: Any, X: Any, y: Any) -> float:
    """Return a ROC AUC score, using the estimator's probability output."""
    if not hasattr(model, "predict_proba"):
        return 0.5
    try:
        probabilities = np.asarray(model.predict_proba(X))
        classes = getattr(model, "classes_", None)
        if probabilities.ndim == 2 and probabilities.shape[1] == 2:
            return float(roc_auc_score(y, probabilities[:, 1]))
        return float(roc_auc_score(y, probabilities, multi_class="ovr",
                                   labels=classes))
    except (ValueError, TypeError):
        return 0.5


def evaluate_classifier(
    model: Any, train_X: Any, train_y: Any, held_out_X: Any = None,
    held_out_y: Any = None, *, average: str = "macro",
) -> dict[str, float]:
    """Score training and optional held-out classification data."""
    if held_out_X is None:
        held_out_X, held_out_y = train_X, train_y
    def score(X, y, prefix):
        predicted = model.predict(X)
        result = {
            f"{prefix}accuracy": float(accuracy_score(y, predicted)),
            f"{prefix}precision": float(precision_score(y, predicted, average=average, zero_division=0)),
            f"{prefix}recall": float(recall_score(y, predicted, average=average, zero_division=0)),
            f"{prefix}f1": float(f1_score(y, predicted, average=average, zero_division=0)),
        }
        return result
    result = score(train_X, train_y, "train_")
    result.update(score(held_out_X, held_out_y, "held_out_"))
    result["train_roc_auc"] = _roc_auc(model, train_X, train_y)
    result["held_out_roc_auc"] = _roc_auc(model, held_out_X, held_out_y)
    result["generalisation_gap"] = result["train_roc_auc"] - result["held_out_roc_auc"]
    return result


def evaluate_text_classifier(
    model: Any,
    train_text: Any,
    train_y: Any,
    held_out_text: Any = None,
    held_out_y: Any = None,
) -> dict[str, Any]:
    """Evaluate a fitted text classifier without refitting it."""
    if held_out_text is None:
        held_out_text, held_out_y = train_text, train_y
    train_predicted = model.predict(train_text)
    held_out_predicted = model.predict(held_out_text)
    labels = list(getattr(model, "classes_", np.unique(train_y)))
    train_f1 = float(f1_score(train_y, train_predicted, average="macro",
                              labels=labels, zero_division=0))
    held_out_f1 = float(f1_score(held_out_y, held_out_predicted, average="macro",
                                 labels=labels, zero_division=0))
    per_class = f1_score(held_out_y, held_out_predicted, average=None,
                         labels=labels, zero_division=0)
    return {
        "train_macro_f1": train_f1,
        "held_out_macro_f1": held_out_f1,
        "generalisation_gap": train_f1 - held_out_f1,
        "per_class_f1": {str(label): float(value) for label, value in zip(labels, per_class)},
    }


def evaluate_regressor(model: Any, train_X: Any, train_y: Any, held_out_X: Any = None,
                       held_out_y: Any = None) -> dict[str, float]:
    if held_out_X is None:
        held_out_X, held_out_y = train_X, train_y
    train_pred = np.asarray(model.predict(train_X), dtype=float)
    held_pred = np.asarray(model.predict(held_out_X), dtype=float)
    baseline = float(np.mean(np.asarray(train_y, dtype=float)))
    held_values = np.asarray(held_out_y, dtype=float)
    result = {
        "train_r2": float(r2_score(train_y, train_pred)),
        "held_out_r2": float(r2_score(held_out_y, held_pred)),
        "generalisation_gap": float(r2_score(train_y, train_pred) - r2_score(held_out_y, held_pred)),
        "mean_absolute_error": float(mean_absolute_error(held_y := held_out_y, held_pred)),
        "average_estimate_mean_absolute_error": float(mean_absolute_error(held_y, np.full(len(held_values), baseline))),
        "lowest_prediction": float(held_pred.min()),
        "train_mae": float(mean_absolute_error(train_y, train_pred)),
        "held_out_mae": float(mean_absolute_error(held_y, held_pred)),
        "rmse": float(np.sqrt(mean_squared_error(held_y, held_pred))),
    }
    return result


def evaluate_model(model: Any, X: Any, y: Any, task: str) -> dict[str, float]:
    if task in {"regression", "regressor", "exposure"}:
        return evaluate_regressor(model, X, y)
    return evaluate_classifier(model, X, y, average="macro" if task == "multiclass" else "binary")


def evaluate_text_classifier(model: Any, train_text: Any, train_y: Any,
                             held_out_text: Any, held_out_y: Any) -> dict[str, Any]:
    """Evaluate a fitted text classifier without refitting it."""
    train_pred = model.predict(train_text)
    held_pred = model.predict(held_out_text)
    labels = sorted({str(value) for value in train_y} | {str(value) for value in held_out_y})
    train_score = float(f1_score(train_y, train_pred, average="macro", zero_division=0))
    held_score = float(f1_score(held_out_y, held_pred, average="macro", zero_division=0))
    per_class = f1_score(held_out_y, held_pred, labels=labels, average=None, zero_division=0)
    return {
        "train_macro_f1": train_score,
        "held_out_macro_f1": held_score,
        "generalisation_gap": train_score - held_score,
        "per_class_f1": {label: float(value) for label, value in zip(labels, per_class)},
    }


classification_metrics = evaluate_classifier
regression_metrics = evaluate_regressor