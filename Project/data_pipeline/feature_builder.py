import pandas as pd
from config import config


def add_slot_minutes(frame):
    frame = frame.copy()
    frame[config.START_MINUTE_COLUMN] = frame[config.START_TIME_COLUMN].map(
        lambda x: int(str(x).split(":")[0]) * 60 + int(str(x).split(":")[1]))
    frame[config.DURATION_MINUTES_COLUMN] = (
        frame[config.END_TIME_COLUMN].map(lambda x: int(str(x).split(":")[0]) * 60 + int(str(x).split(":")[1]))
        - frame[config.START_MINUTE_COLUMN])
    return frame


def build_feature_frame(frame, numeric_columns, categorical_columns):
    result = pd.DataFrame(index=frame.index)
    for col in numeric_columns:
        result[col] = pd.to_numeric(frame[col], errors="coerce").astype(float)
    for col in categorical_columns:
        result[col] = frame[col].replace({"": pd.NA})
    return result