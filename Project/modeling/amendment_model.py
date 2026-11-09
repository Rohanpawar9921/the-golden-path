"""Model for predicting whether a submission needs amendment."""

from __future__ import annotations

import pandas as pd

from config import config
from ._common import classifier, frame_with_features

FEATURES = config.AMENDMENT_NUMERIC_FEATURES + config.AMENDMENT_CATEGORICAL_FEATURES


def train_amendment_model(data: pd.DataFrame):
    target_name = config.SUBMISSION_TARGET_COLUMN
    if target_name not in data:
        raise ValueError(f"Missing target column: {target_name}")
    frame = data.dropna(subset=[target_name])
    target = pd.to_numeric(frame[target_name].replace(config.SUBMISSION_TARGET_ENCODING), errors="coerce")
    valid = target.notna()
    model = classifier(config.AMENDMENT_NUMERIC_FEATURES, config.AMENDMENT_CATEGORICAL_FEATURES, target[valid])
    model.fit(frame_with_features(frame.loc[valid], FEATURES, config.AMENDMENT_NUMERIC_FEATURES), target[valid].astype(int))
    model.feature_schema = FEATURES
    return model


def predict_amendment(model, data: pd.DataFrame):
    return model.predict(frame_with_features(data, FEATURES, config.AMENDMENT_NUMERIC_FEATURES))


def predict_amendment_probability(model, data: pd.DataFrame):
    X = frame_with_features(data, FEATURES, config.AMENDMENT_NUMERIC_FEATURES)
    return model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else model.predict(X)