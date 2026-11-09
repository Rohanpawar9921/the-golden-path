"""Shared construction utilities for the three model types."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor


def frame_with_features(
    data: pd.DataFrame, features: Iterable[str], numeric: Iterable[str] = ()
) -> pd.DataFrame:
    result = data.copy()
    features = list(features)
    for column in features:
        if column not in result:
            result[column] = None
    result = result.loc[:, features].replace({pd.NA: np.nan, None: np.nan})
    for column in numeric:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("numeric", SimpleImputer(strategy="median", add_indicator=True), numeric),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="constant", fill_value="__missing__")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )


def classifier(numeric: list[str], categorical: list[str], y: pd.Series) -> Pipeline:
    estimator = (
        LogisticRegression(max_iter=1500, random_state=42)
        if y.nunique(dropna=True) > 1
        else DummyClassifier(strategy="most_frequent")
    )
    return Pipeline([("preprocessor", preprocessor(numeric, categorical)), ("model", estimator)])


def regressor(numeric: list[str], categorical: list[str], y: pd.Series) -> Pipeline:
    estimator = (
        RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1, min_samples_leaf=1)
        if len(y) > 1
        else DummyRegressor(strategy="mean")
    )
    return Pipeline([("preprocessor", preprocessor(numeric, categorical)), ("model", estimator)])
