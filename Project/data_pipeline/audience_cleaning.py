import re
import pandas as pd
from config import config
from .common_cleaning import deduplicate_and_require_target, normalise_values, write_frame, clean_numeric


def _clock(value):
    m = re.fullmatch(config.CLOCK_TIME_PATTERN, str(value).strip())
    if not m:
        raise ValueError(f"Unrecognised time: {value!r}")
    return int(m.group(1)) * 60 + int(m.group(2))


def clean_audience_dataset(input_path, output_path):
    frame = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    frame = normalise_values(frame, config.AUDIENCE_VALUE_MAPPINGS)
    frame = clean_numeric(frame, config.AUDIENCE_WHOLE_NUMBER_PATTERNS, config.AUDIENCE_RANGE_LIMITS)
    for column in ["audience_all", "under18_viewers"]:
        if column in frame:
            values = []
            for value in frame[column]:
                original = str(value).strip().lower()
                text = original.replace(",", "")
                if not text or text in [x.lower() for x in config.NULL_TOKENS]:
                    values.append(pd.NA)
                elif re.fullmatch(config.VIEWERS_NOTATION_PATTERN, original):
                    values.append(float(text.replace(",", "")) / 1000)
                elif re.fullmatch(config.MILLIONS_NOTATION_PATTERN, text):
                    values.append(float(re.match(r"-?\d+(?:\.\d+)?", text).group()) * 1000)
                elif re.fullmatch(config.THOUSANDS_NOTATION_PATTERN, text):
                    values.append(float(re.match(r"-?\d+(?:\.\d+)?", text).group()))
                elif re.fullmatch(config.PLAIN_NUMBER_PATTERN, text):
                    values.append(float(text))
                else:
                    raise ValueError(f"Unrecognised audience value: {value!r}")
            frame[column] = pd.Series(values, index=frame.index, dtype="Float64")
            low, high = config.AUDIENCE_RANGE_LIMITS[column]
            frame.loc[frame[column].notna() & ((frame[column] < low) | (frame[column] > high)), column] = pd.NA
            frame[column] = frame[column].round(config.AUDIENCE_DECIMALS)
    for idx, row in frame.iterrows():
        system = str(row.get(config.SCHEDULING_SYSTEM_COLUMN, ""))
        if system not in config.BROADCAST_CLOCK_SYSTEMS + config.CALENDAR_CLOCK_SYSTEMS:
            raise ValueError(f"Unknown scheduling system: {system!r}")
        day = row[config.TRANSMISSION_DAY_COLUMN]
        start, end = _clock(row[config.START_TIME_COLUMN]), _clock(row[config.END_TIME_COLUMN])
        if system in config.CALENDAR_CLOCK_SYSTEMS and (start >= config.MINUTES_PER_DAY
                                                        or end >= config.MINUTES_PER_DAY):
            raise ValueError("Calendar clock cannot contain 24-hour times")
        if system in config.CALENDAR_CLOCK_SYSTEMS:
            if start < config.BROADCAST_DAY_START_MINUTE:
                day = config.PREVIOUS_WEEKDAY[day]
                start += config.MINUTES_PER_DAY
            if end < config.BROADCAST_DAY_START_MINUTE or end <= start:
                end += config.MINUTES_PER_DAY
        elif start < config.BROADCAST_DAY_START_MINUTE or end < start:
            raise ValueError("Invalid broadcast-clock time")
        if end <= start:
            raise ValueError("End time must follow start time")
        frame.at[idx, config.TRANSMISSION_DAY_COLUMN] = day
        frame.at[idx, config.START_TIME_COLUMN] = f"{start // 60:02d}:{start % 60:02d}"
        frame.at[idx, config.END_TIME_COLUMN] = f"{end // 60:02d}:{end % 60:02d}"
    frame = deduplicate_and_require_target(frame, "airing_id", config.AUDIENCE_TARGET_COLUMN)
    frame[config.AUDIENCE_TARGET_COLUMN] = pd.to_numeric(frame[config.AUDIENCE_TARGET_COLUMN], errors="coerce")
    frame = frame[frame[config.AUDIENCE_TARGET_COLUMN].notna() & (frame[config.AUDIENCE_TARGET_COLUMN] >= 0)]
    write_frame(frame, output_path)
    return frame