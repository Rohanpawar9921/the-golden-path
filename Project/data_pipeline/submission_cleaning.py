import re
import pandas as pd
from config import config
from .common_cleaning import (deduplicate_and_require_target, normalise_values, write_frame,
                              clean_numeric)


def _spot_seconds(value):
    text = str(value).strip().lower()
    if not text or text in [x.lower() for x in config.NULL_TOKENS]:
        return pd.NA
    if re.fullmatch(config.SECONDS_NOTATION_PATTERN, text):
        return int(re.match(r"\d+", text).group())
    if m := re.fullmatch(config.MINUTES_AND_SECONDS_NOTATION_PATTERN, text):
        return int(m.group(1)) * 60 + int(m.group(2))
    if m := re.fullmatch(config.HOURS_MINUTES_AND_SECONDS_NOTATION_PATTERN, text):
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    raise ValueError(f"Unrecognised spot length: {value!r}")


def clean_submission_dataset(input_path, output_path):
    frame = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    frame = normalise_values(frame, config.SUBMISSION_VALUE_MAPPINGS)
    if config.CLOCK_NUMBER_COLUMN in frame:
        lengths = frame[config.CLOCK_NUMBER_COLUMN].str.extract(config.CLOCK_NUMBER_PATTERN, expand=False)
        if lengths.isna().any():
            raise ValueError("Invalid clock number")
        parsed = frame[config.COPY_LENGTH_COLUMN].map(_spot_seconds)
        clock_length = pd.to_numeric(lengths, errors="coerce")
        if not clock_length.isin(config.STANDARD_SPOT_LENGTHS).all():
            raise ValueError("Unsupported spot length in clock number")
        frame[config.COPY_LENGTH_COLUMN] = parsed
        frame.loc[clock_length.notna(), config.COPY_LENGTH_COLUMN] = clock_length[clock_length.notna()]
    frame = clean_numeric(frame, config.SUBMISSION_WHOLE_NUMBER_PATTERNS,
                          config.SUBMISSION_RANGE_LIMITS)
    frame = clean_numeric(frame, config.SUBMISSION_DECIMAL_NUMBER_PATTERNS,
                          config.SUBMISSION_RANGE_LIMITS)
    for col in ["legal_text_seconds", "advertiser_amendments_past_year"]:
        if col in frame and config.COPY_LENGTH_COLUMN in frame:
            bad = frame[col].notna() & (frame[col] > frame[config.COPY_LENGTH_COLUMN])
            frame.loc[bad, col] = pd.NA
    if {"advertiser_campaigns_past_year", "advertiser_amendments_past_year"} <= set(frame):
        bad = frame["advertiser_amendments_past_year"].notna() & frame["advertiser_campaigns_past_year"].notna() & (frame["advertiser_amendments_past_year"] > frame["advertiser_campaigns_past_year"])
        frame.loc[bad, "advertiser_amendments_past_year"] = pd.NA
    frame = deduplicate_and_require_target(frame, "submission_id", config.SUBMISSION_TARGET_COLUMN)
    frame[config.SUBMISSION_TARGET_COLUMN] = frame[config.SUBMISSION_TARGET_COLUMN].map(
        lambda x: config.BOOLEAN_MAPPING.get(str(x).strip().lower(), str(x).strip()))
    write_frame(frame, output_path)
    return frame