import pandas as pd


def profile_dataset(raw_frame, clean_frame, target_column):
    target = raw_frame[target_column].astype("string")
    missing_mask = target.isna() | target.str.strip().eq("")
    missing_target = int(missing_mask[~raw_frame.duplicated(keep="first")].sum())
    other_removed = 0
    numeric_target = pd.to_numeric(target, errors="coerce")
    if numeric_target.notna().any():
        other_removed += int((numeric_target < 0).sum())
    if "note_text" in raw_frame:
        other_removed += int((raw_frame["note_text"].astype(str).str.split().str.len()
                              < 6).sum())
    duplicate_rows = int(len(raw_frame) - len(clean_frame) - missing_target - other_removed)
    missing_received = {c: int(raw_frame[c].isna().sum() + raw_frame[c].astype("string").eq("").sum())
                        for c in raw_frame.columns if raw_frame[c].isna().any() or raw_frame[c].astype("string").eq("").any()}
    missing_clean = {c: int(clean_frame[c].isna().sum() + clean_frame[c].astype("string").eq("").sum())
                     for c in clean_frame.columns if clean_frame[c].isna().any() or clean_frame[c].astype("string").eq("").any()}
    return {"rows_received": len(raw_frame), "rows_kept": len(clean_frame),
            "rows_removed": len(raw_frame) - len(clean_frame),
            "duplicate_rows": duplicate_rows, "rows_missing_target": missing_target,
            "columns": int(clean_frame.shape[1]),
            "missing_cells_as_received": missing_received,
            "missing_cells_after_cleaning": missing_clean}