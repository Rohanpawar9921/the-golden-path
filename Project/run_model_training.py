"""Train and persist the clearance prediction models."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from config import config
from modeling.amendment_model import train_amendment_model
from modeling.exposure_model import train_exposure_model
from modeling.issue_model import train_issue_model
from modeling.model_evaluation import evaluate_classifier, evaluate_regressor
from modeling.model_registry import save_metrics, save_model, save_schema, load_model
from data_pipeline.feature_builder import add_slot_minutes


ROOT = Path(__file__).resolve().parent


def _read(configured: str, fallback: str) -> pd.DataFrame:
    path = ROOT / configured
    if not path.exists():
        path = ROOT / fallback
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {configured}")
    return pd.read_csv(path)


def main() -> dict:
    submissions = _read(config.CLEAN_SUBMISSIONS_TRAIN_FILE, config.RAW_SUBMISSIONS_TRAIN_FILE).head(6000)
    submissions_eval = _read(config.CLEAN_SUBMISSIONS_EVAL_FILE, config.RAW_SUBMISSIONS_EVAL_FILE)
    audiences = add_slot_minutes(_read(config.CLEAN_AUDIENCES_TRAIN_FILE, config.RAW_AUDIENCES_TRAIN_FILE))
    audiences_eval = add_slot_minutes(_read(config.CLEAN_AUDIENCES_EVAL_FILE, config.RAW_AUDIENCES_EVAL_FILE))
    notes = _read(config.CLEAN_CLEARANCE_NOTES_FILE, config.RAW_CLEARANCE_NOTES_FILE)

    amendment = train_amendment_model(submissions)
    exposure = train_exposure_model(audiences)
    issue = train_issue_model(notes)

    metrics = {"amendment": {}, "exposure": {}, "issue": {}}
    if config.SUBMISSION_TARGET_COLUMN in submissions_eval:
        target = pd.to_numeric(
            submissions_eval[config.SUBMISSION_TARGET_COLUMN].replace(config.SUBMISSION_TARGET_ENCODING),
            errors="coerce",
        )
        valid = target.notna()
        metrics["amendment"] = evaluate_classifier(
            amendment,
            submissions.drop(columns=[config.SUBMISSION_TARGET_COLUMN], errors="ignore"),
            pd.to_numeric(submissions[config.SUBMISSION_TARGET_COLUMN].replace(config.SUBMISSION_TARGET_ENCODING), errors="coerce").astype(int),
            submissions_eval.loc[valid].drop(columns=[config.SUBMISSION_TARGET_COLUMN], errors="ignore"),
            target[valid].astype(int),
            average="binary",
        )
    if config.AUDIENCE_TARGET_COLUMN in audiences_eval:
        eval_target = pd.to_numeric(audiences_eval[config.AUDIENCE_TARGET_COLUMN], errors="coerce")
        eval_valid = eval_target.notna()
        metrics["exposure"] = evaluate_regressor(
            exposure,
            audiences.drop(columns=[config.AUDIENCE_TARGET_COLUMN], errors="ignore"),
            pd.to_numeric(audiences[config.AUDIENCE_TARGET_COLUMN], errors="coerce"),
            audiences_eval.loc[eval_valid].drop(columns=[config.AUDIENCE_TARGET_COLUMN], errors="ignore"),
            eval_target[eval_valid],
        )

    output = ROOT / config.MODEL_METRICS_FILE
    save_model(amendment, ROOT / config.AMENDMENT_MODEL_FILE)
    save_model(exposure, ROOT / config.EXPOSURE_MODEL_FILE)
    save_model(issue, ROOT / config.ISSUE_MODEL_FILE)
    save_schema(amendment.feature_schema, ROOT / config.AMENDMENT_SCHEMA_FILE)
    save_schema(exposure.feature_schema, ROOT / config.EXPOSURE_SCHEMA_FILE)
    # Score the serialized artifacts, not the in-memory estimators.  This keeps
    # the metrics file authoritative for exactly what pytest/application loads.
    saved_amendment = load_model(config.AMENDMENT_MODEL_FILE)
    train_X = __import__("data_pipeline.feature_builder", fromlist=["build_feature_frame"]).build_feature_frame(
        submissions.copy(), config.AMENDMENT_NUMERIC_FEATURES,
        config.AMENDMENT_CATEGORICAL_FEATURES)[saved_amendment.feature_schema]
    eval_X = __import__("data_pipeline.feature_builder", fromlist=["build_feature_frame"]).build_feature_frame(
        submissions_eval.loc[valid].copy(), config.AMENDMENT_NUMERIC_FEATURES,
        config.AMENDMENT_CATEGORICAL_FEATURES)[saved_amendment.feature_schema]
    train_y = pd.to_numeric(submissions[config.SUBMISSION_TARGET_COLUMN].replace(config.SUBMISSION_TARGET_ENCODING), errors="coerce").astype(int)
    eval_y = target[valid].astype(int)
    metrics["amendment"] = evaluate_classifier(saved_amendment, train_X, train_y,
                                                eval_X, eval_y, average="binary")
    save_metrics(metrics, output)
    return metrics


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))