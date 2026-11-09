"""Persistence helpers for trained models and their metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib


def _path(path: str | Path) -> Path:
    result = Path(path)
    result.parent.mkdir(parents=True, exist_ok=True)
    return result


def save_model(model: Any, path: str | Path) -> str:
    """Persist a fitted sklearn estimator and return its path."""
    target = _path(path)
    joblib.dump(model, target)
    return str(target)


def load_model(path: str | Path) -> Any:
    return joblib.load(path)


def save_schema(schema: Any, path: str | Path) -> str:
    target = _path(path)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(schema, handle, indent=2, default=str)
    return str(target)


def load_schema(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_feature_schema(path: str | Path) -> list[str]:
    """Load a feature-column schema in the public, column-list format.

    Older artifacts stored ``numeric`` and ``categorical`` lists in a mapping;
    accepting that representation keeps existing model directories readable.
    """
    schema = load_schema(path)
    if isinstance(schema, dict):
        if "features" in schema:
            return list(schema["features"])
        return list(schema.get("numeric", [])) + list(schema.get("categorical", []))
    return list(schema)


def save_metrics(metrics: Mapping[str, Any], path: str | Path) -> str:
    target = _path(path)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(dict(metrics), handle, indent=2, default=float)
    return str(target)


def load_metrics(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


# Explicit names are useful to callers that prefer registry terminology.
register_model = save_model
get_model = load_model