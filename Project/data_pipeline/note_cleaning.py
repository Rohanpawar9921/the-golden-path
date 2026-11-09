import html
import re
import pandas as pd
from config import config
from .common_cleaning import deduplicate_and_require_target, normalise_values, write_frame, clean_numeric


def _clean_text(value):
    text = html.unescape(str(value))
    text = re.sub(config.MARKUP_PATTERN, " ", text).replace(config.NO_BREAK_SPACE, " ")
    return re.sub(config.WHITESPACE_RUN_PATTERN, " ", text).strip().lower()


def _clean_time(value):
    m = re.fullmatch(config.NOTE_TIMESTAMP_PATTERN, str(value).strip())
    if not m or m.group(config.NOTE_WEEKDAY_PART).lower() not in config.WEEKDAY_MAPPING:
        raise ValueError(f"Unrecognised note timestamp: {value!r}")
    day = config.WEEKDAY_MAPPING[m.group(config.NOTE_WEEKDAY_PART).lower()]
    return f"{day} {m.group(config.NOTE_TIME_PART)}"


def clean_note_dataset(input_path, output_path):
    frame = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    frame = normalise_values(frame, config.NOTE_VALUE_MAPPINGS)
    frame[config.NOTE_TEXT_COLUMN] = frame[config.NOTE_TEXT_COLUMN].map(_clean_text)
    frame[config.NOTE_TIMESTAMP_COLUMN] = frame[config.NOTE_TIMESTAMP_COLUMN].map(_clean_time)
    frame[config.NOTE_LENGTH_COLUMN] = frame[config.NOTE_TEXT_COLUMN].str.len()
    frame = clean_numeric(frame, config.NOTE_WHOLE_NUMBER_PATTERNS)
    frame = deduplicate_and_require_target(frame, "note_id", config.NOTE_TARGET_COLUMN)
    frame = frame[frame[config.NOTE_TEXT_COLUMN].str.split().str.len() >= config.MINIMUM_NOTE_WORDS]
    write_frame(frame, output_path)
    return frame