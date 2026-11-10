# Know Your Data

A short guide to the data cleaning and model training flow in BreakCheck.

> **Counts are a snapshot** from the supplied CSV files and the current `output/data_quality_report.json`. If the inputs change, rerun the pipeline to refresh the counts.

## 1. What data goes in?

| Input file | What it contains | Rows received | Columns | Target used by a model |
|---|---|---:|---:|---|
| `data/campaign_submissions_train.csv` | Past campaign submissions used to learn amendment patterns | 30,706 | 38 | `amendment_required` — Yes or No |
| `data/campaign_submissions_eval.csv` | Held-out submissions used to check amendment predictions | 8,514 | 38 | `amendment_required` — Yes or No |
| `data/programme_audiences_train.csv` | Programme scheduling and audience observations used to learn audience estimates | 30,877 | 21 | `under18_viewers` — a number, in thousands |
| `data/programme_audiences_eval.csv` | Held-out audience observations used to check audience estimates | 7,004 | 21 | `under18_viewers` — a number, in thousands |
| `data/clearance_notes.csv` | Past clearance notes and their issue labels | 34,727 | 13 | `issue_category` — one of eight issue types |

The `train` and `eval` files are supplied separately; the project does not create these splits. The training script evaluates the amendment and audience models on the corresponding `eval` files. There is no separate evaluation file for clearance notes: the current script trains the issue model on all cleaned notes and does not report an issue-model evaluation score.

The files in `data/input/` (`open_campaigns.csv`, `booked_spots.csv`, `programme_schedule.csv`, and `open_campaign_notes.csv`) supply the live campaign queue and tools. They are not the five inputs cleaned by `run_data_pipeline.py` above.

## 2. How many empty values are there?

An **empty cell** means a blank field in the supplied CSV. A **row with an empty value** has at least one blank cell. A **fully empty row** has no values in any column. There are no fully empty rows in these five files. A row with one missing feature is not automatically removed.

| Raw input | Empty cells | Rows with at least one empty cell | Fully empty rows |
|---|---:|---:|---:|
| `campaign_submissions_train.csv` | 34,162 | 24,810 | 0 |
| `campaign_submissions_eval.csv` | 9,400 | 6,846 | 0 |
| `programme_audiences_train.csv` | 6,926 | 6,848 | 0 |
| `programme_audiences_eval.csv` | 1,570 | 1,553 | 0 |
| `clearance_notes.csv` | 155 | 155 | 0 |

Some feature values remain missing after cleaning. These are not empty rows; they are individual feature cells that the model preprocessing handles.

| Cleaned output | Empty feature cells remaining | Rows with at least one missing feature |
|---|---:|---:|
| `campaign_submissions_train_clean.csv` | 39,238 | 25,601 |
| `campaign_submissions_eval_clean.csv` | 10,749 | 7,070 |
| `programme_audiences_train_clean.csv` | 9,744 | 9,578 |
| `programme_audiences_eval_clean.csv` | 2,228 | 2,188 |
| `clearance_notes_clean.csv` | 99 | 99 |

Some fields are intentionally left empty when their value is not known or does not apply. The models handle remaining missing feature values: numeric fields are filled with the training median and get a missing-value indicator; categorical fields receive a `__missing__` category.

## 3. What does cleaning do?

| Data | Main cleaning steps |
|---|---|
| Submissions | Standardizes category, channel, weekday, and Yes/No spellings; parses counts, percentages, and spot lengths; uses the recognized clock number when it gives the standard spot length; marks impossible values missing (for example, legal text longer than the copy or amendments greater than campaigns); removes duplicate submission IDs and rows without an amendment target. |
| Programme audiences | Standardizes channel, genre, weekday, scheduling-system, and flag values; converts audience notations such as `k`, `thousand`, commas, and `m` into numbers in thousands; checks numeric ranges; converts calendar times to the broadcast clock (including after-midnight times); removes duplicate airing IDs, missing targets, and negative audience targets. |
| Clearance notes | Standardizes category labels and author/source values; removes HTML entities and markup, normalizes whitespace and case, cleans the written timestamp, recalculates note length from the cleaned text, removes duplicate note IDs, missing issue targets, and notes shorter than six words. |

All three cleaners preserve the supplied raw files. They write cleaned CSVs and the pipeline records rows received/kept/removed, duplicates, missing targets, and missing cells in the quality report.

## 4. How many rows remain?

| Data set | Rows received | Rows kept | Rows removed | Main recorded removal counts |
|---|---:|---:|---:|---|
| Submissions — train | 30,706 | 29,697 | 1,009 | 814 duplicate IDs; 195 missing targets |
| Submissions — eval | 8,514 | 8,224 | 290 | 236 duplicate IDs; 54 missing targets |
| Audiences — train | 30,877 | 29,817 | 1,060 | 778 duplicate IDs; 187 missing targets; 95 impossible targets |
| Audiences — eval | 7,004 | 6,770 | 234 | 189 duplicate IDs; 28 missing targets; 17 impossible targets |
| Clearance notes | 34,727 | 33,045 | 1,682 | 816 duplicate IDs; 186 missing targets; 680 notes under six words |

These counts explain removed records. Other missing feature values can remain in kept rows and are handled by the model imputers described above.

## 5. What files come out?

| Output | What it is |
|---|---|
| `processed/campaign_submissions_train_clean.csv` | Cleaned training submissions |
| `processed/campaign_submissions_eval_clean.csv` | Cleaned evaluation submissions |
| `processed/programme_audiences_train_clean.csv` | Cleaned training audience records |
| `processed/programme_audiences_eval_clean.csv` | Cleaned evaluation audience records |
| `processed/clearance_notes_clean.csv` | Cleaned clearance notes |
| `output/data_quality_report.json` | Cleaning counts and missing-value report for each input |
| `output/models/amendment_model.pkl` | Saved amendment classifier |
| `output/models/amendment_features.json` | Amendment model feature order |
| `output/models/exposure_model.pkl` | Saved under-18 audience regressor |
| `output/models/exposure_features.json` | Exposure model feature order |
| `output/models/issue_model.pkl` | Saved note issue classifier |
| `output/model_metrics.json` | Evaluation metrics for the amendment and exposure models |

## 6. Which targets and models are used?

| Model | Target column | In simple terms | Current algorithm |
|---|---|---|---|
| Amendment | `amendment_required` | Predict whether a submission needs amendment (Yes/No) | Logistic regression with median imputation and missing indicators for numeric features, plus missing-category filling and one-hot encoding for categories. If training has only one target class, it falls back to a most-frequent-class predictor. |
| Exposure | `under18_viewers` | Estimate the under-18 audience for a programme slot (numeric, in thousands) | Random forest regressor with 150 trees, numeric imputation, and one-hot encoded categories. If training has only one row, it falls back to a mean predictor. |
| Issue | `issue_category` | Classify the issue described in a clearance note | TF-IDF text features using one- and two-word phrases, followed by balanced logistic regression. If training has only one issue class, it falls back to a most-frequent-class predictor. |

The eight cleaned issue labels are: Health claim; Price or offer claim; Appeal to under-18s; Financial promotion; Alcohol and social success; Gambling inducement; Comparative claim; Environmental claim.

**Training detail:** `run_model_training.py` currently fits the amendment model on the first 6,000 rows of the cleaned submission training file. It uses the supplied evaluation file to measure amendment performance. The exposure model uses the cleaned audience training file and its supplied evaluation file. The issue model uses all cleaned clearance notes; there is no separate note evaluation split in the current training script.

## 7. Commands to rebuild the outputs

Run these from the `Project` folder in PowerShell:

| Command | Why |
|---|---|
| `python run_data_pipeline.py` | Clean the five raw data files and refresh `processed/` and `output/data_quality_report.json`. |
| `python run_model_training.py` | Train the three models and refresh the model files and metrics. |

