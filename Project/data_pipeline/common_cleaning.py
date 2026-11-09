"""Shared, deliberately conservative cleaning helpers for the supplied extracts."""
import re
import pandas as pd
from config import config


def _text(value):
    return "" if pd.isna(value) else str(value).strip()


def normalise_values(frame, mappings):
    frame = frame.copy()
    for column, mapping in mappings.items():
        if column in frame:
            frame[column] = frame[column].map(
                lambda value: mapping.get(_text(value).lower(), _text(value)) if _text(value) else pd.NA
            )
    return frame


def parse_number(value, pattern):
    text = _text(value).lower().replace(",", "")
    if not text or text in {token.lower() for token in config.NULL_TOKENS}:
        return pd.NA
    match = re.fullmatch(pattern, text)
    if not match:
        raise ValueError(f"Unrecognised numeric value: {value!r}")
    return float(match.group(1) if match.lastindex else match.group(0))


def clean_numeric(frame, patterns, ranges=None):
    frame = frame.copy()
    for column, pattern in patterns.items():
        if column not in frame:
            continue
        values = []
        for value in frame[column]:
            try:
                parsed = parse_number(value, pattern)
            except ValueError:
                raise
            values.append(parsed)
        frame[column] = pd.Series(values, index=frame.index, dtype="Float64")
        if ranges and column in ranges:
            low, high = ranges[column]
            invalid = frame[column].notna() & ((frame[column] < low) | (frame[column] > high))
            frame.loc[invalid, column] = pd.NA
    return frame


def deduplicate_and_require_target(frame, identifier, target):
    frame = frame.copy()
    target_text = frame[target].map(_text)
    answered = ~target_text.str.lower().isin([x.lower() for x in config.NULL_TOKENS])
    frame = frame.loc[answered].drop_duplicates(identifier, keep="first").copy()
    return frame


def write_frame(frame, path):
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    frame.to_csv(path, index=False)