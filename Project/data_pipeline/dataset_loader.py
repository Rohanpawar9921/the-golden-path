"""Loading entry point used by both the batch pipeline and live tools."""
import pandas as pd


def load_raw_dataset(file_path):
    return pd.read_csv(file_path, dtype=str, keep_default_na=False, na_values=[""],
                       low_memory=False)