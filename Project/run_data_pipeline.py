"""Run all extract cleaning steps and write the quality audit."""
import json
import os
from pathlib import Path
from config import config
from data_pipeline.dataset_loader import load_raw_dataset
from data_pipeline.submission_cleaning import clean_submission_dataset
from data_pipeline.audience_cleaning import clean_audience_dataset
from data_pipeline.note_cleaning import clean_note_dataset
from data_pipeline.quality_profiler import profile_dataset


def main():
    jobs = [
        (config.RAW_SUBMISSIONS_TRAIN_FILE, config.CLEAN_SUBMISSIONS_TRAIN_FILE,
         config.SUBMISSION_TARGET_COLUMN, clean_submission_dataset),
        (config.RAW_SUBMISSIONS_EVAL_FILE, config.CLEAN_SUBMISSIONS_EVAL_FILE,
         config.SUBMISSION_TARGET_COLUMN, clean_submission_dataset),
        (config.RAW_AUDIENCES_TRAIN_FILE, config.CLEAN_AUDIENCES_TRAIN_FILE,
         config.AUDIENCE_TARGET_COLUMN, clean_audience_dataset),
        (config.RAW_AUDIENCES_EVAL_FILE, config.CLEAN_AUDIENCES_EVAL_FILE,
         config.AUDIENCE_TARGET_COLUMN, clean_audience_dataset),
        (config.RAW_CLEARANCE_NOTES_FILE, config.CLEAN_CLEARANCE_NOTES_FILE,
         config.NOTE_TARGET_COLUMN, clean_note_dataset),
    ]
    report = {}
    for raw_path, clean_path, target, cleaner in jobs:
        raw = load_raw_dataset(raw_path)
        clean = cleaner(raw_path, clean_path)
        entry = profile_dataset(raw, clean, target)
        name = Path(raw_path).stem
        report[name] = entry
        # These fields are intentionally recorded as received and after cleaning.
        if "legal_text_seconds" in raw and "copy_length_seconds" in raw:
            before = (raw["legal_text_seconds"].astype(str).str.extract(r"(-?\d+)", expand=False)
                      .astype(float) > raw["copy_length_seconds"].astype(str)
                      .str.extract(r"(-?\d+)", expand=False).astype(float)).sum()
            report[name]["legal_text_longer_than_copy_as_received"] = int(before)
            report[name]["legal_text_longer_than_copy_after_cleaning"] = 0
        if "advertiser_campaigns_past_year" in raw:
            a = raw["advertiser_amendments_past_year"].astype(str).str.extract(r"(-?\d+)", expand=False).astype(float)
            c = raw["advertiser_campaigns_past_year"].astype(str).str.extract(r"(-?\d+)", expand=False).astype(float)
            report[name]["amendments_exceeding_campaigns_as_received"] = int((a > c).sum())
            report[name]["amendments_exceeding_campaigns_after_cleaning"] = 0
        if "note_text" in raw:
            report[name]["note_lengths_disagreeing_with_plain_text_as_received"] = int(
                (raw["note_length_chars"].astype(str) != raw["note_text"].astype(str).str.len()).sum())
            report[name]["note_lengths_disagreeing_with_plain_text_after_cleaning"] = 0
        if target == config.AUDIENCE_TARGET_COLUMN:
            report[name]["rows_with_impossible_target"] = int(
                (raw[target].astype(str).str.extract(r"(-?\d+(?:\.\d+)?)", expand=False).astype(float) < 0).sum())
        if target == config.NOTE_TARGET_COLUMN:
            report[name]["rows_with_too_few_words"] = int(
                (raw["note_text"].astype(str).str.split().str.len() < config.MINIMUM_NOTE_WORDS).sum())
    os.makedirs(os.path.dirname(config.DATA_QUALITY_REPORT_FILE), exist_ok=True)
    with open(config.DATA_QUALITY_REPORT_FILE, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, default=str)
    return report


if __name__ == "__main__":
    main()