"""Model for categorising clearance-note issues."""

from __future__ import annotations

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from config import config


def train_issue_model(data: pd.DataFrame):
    target_name, text_name = config.NOTE_TARGET_COLUMN, config.NOTE_TEXT_COLUMN
    if target_name not in data:
        raise ValueError(f"Missing target column: {target_name}")
    frame = data.dropna(subset=[target_name])
    y = frame[target_name].astype(str)
    estimator = LogisticRegression(max_iter=1500, class_weight="balanced", random_state=config.RANDOM_SEED)
    if y.nunique() < 2:
        estimator = DummyClassifier(strategy="most_frequent")
    model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)), ("model", estimator)])
    model.fit(frame.get(text_name, pd.Series("", index=frame.index)).fillna("").astype(str), y)
    model.feature_schema = {"text": text_name, "target": target_name}
    return model


def predict_issue(model, data: pd.DataFrame):
    text_name = getattr(model, "feature_schema", {}).get("text", config.NOTE_TEXT_COLUMN)
    return model.predict(data.get(text_name, pd.Series("", index=data.index)).fillna("").astype(str))