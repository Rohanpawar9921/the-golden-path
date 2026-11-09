"""Model for estimating under-18 programme audience exposure."""

from __future__ import annotations

import pandas as pd

from config import config
from ._common import frame_with_features, regressor

FEATURES = config.EXPOSURE_NUMERIC_FEATURES + config.EXPOSURE_CATEGORICAL_FEATURES


def train_exposure_model(data: pd.DataFrame):
    target_name = config.AUDIENCE_TARGET_COLUMN
    if target_name not in data:
        raise ValueError(f"Missing target column: {target_name}")
    frame = data.copy()
    target = pd.to_numeric(frame[target_name], errors="coerce")
    valid = target.notna()
    model = regressor(config.EXPOSURE_NUMERIC_FEATURES, config.EXPOSURE_CATEGORICAL_FEATURES, target[valid])
    model.fit(frame_with_features(frame.loc[valid], FEATURES, config.EXPOSURE_NUMERIC_FEATURES), target[valid])
    model.feature_schema = FEATURES
    return model


def predict_exposure(model, data: pd.DataFrame):
    return model.predict(frame_with_features(data, FEATURES, config.EXPOSURE_NUMERIC_FEATURES))