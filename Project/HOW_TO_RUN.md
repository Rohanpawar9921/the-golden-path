# How to Run the Project

This guide explains how to install, prepare, test, and run the BreakCheck project on Windows.

## 1. Open the project directory

Open PowerShell and run:

```powershell
cd "D:\Downloads\workspace-source-20261109-102912\workspace\Project"
```

The commands below assume that the current directory is `Project`.

## 2. Create and activate a virtual environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, run PowerShell as permitted by your local policy or use
the virtual-environment interpreter directly.

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The first installation may take time because document indexing and machine-learning
dependencies include PyTorch and sentence-transformers.

## 4. Configure environment variables

Copy the safe template and add your newly generated credential:

```powershell
Copy-Item .env.example .env
```

The project reads `.env` from the `Project` directory. Never commit `.env`; the
repository `.gitignore` excludes it. Do not commit secrets or replace values with
publicly visible credentials.

The Gemini variables configure generated answers from the clearance assistant. When the
Gemini service is unavailable or disabled for testing, the assistant shows a clearly marked
excerpt selected from the retrieved policy documents instead of inventing an answer.

## 5. Prepare project data

Run the data pipeline:

```powershell
python run_data_pipeline.py
```

This creates the cleaned datasets under `processed\` and the quality report under
`output\`.

Create and seed the local database:

```powershell
python run_database_setup.py
```

If the supplied policy PDFs are present and the knowledge index needs to be rebuilt, run:

```powershell
python run_knowledge_indexing.py
```

## 6. Train the models

```powershell
python run_model_training.py
```

Model files, schemas, and metrics are written under `output\models\` and `output\`.

## 7. Run the tests

From the `Project` directory:

```powershell
$env:BREAKCHECK_CHAT_OFFLINE = "1"
python -m pytest ..\pytest\tests.py tests -q
Remove-Item Env:BREAKCHECK_CHAT_OFFLINE
```

This keeps acceptance tests repeatable and avoids calling the configured model. Omit the
offline variable when manually checking live generated answers.

The test suite is the acceptance contract for the project. A successful run currently
reports all tests passing.

## 8. Start the API service

To run preparation and start the API with one command:

```powershell
.\run_project.ps1
```

To skip rebuilding the knowledge index or models:

```powershell
.\run_project.ps1 -SkipKnowledgeIndex -SkipModelTraining
```

To also start the dashboard:

```powershell
.\run_project.ps1 -StartDashboard
```

The script uses `.venv\Scripts\python.exe` when the virtual environment exists.

Alternatively, run the API directly:

Run:

```powershell
python run_api_service.py
```

If the entry-point file does not start Uvicorn in your environment, start the FastAPI
application explicitly:

```powershell
python -m uvicorn api.routes:service_application --host 127.0.0.1 --port 8000
```

The API is then available at:

- API base URL: `http://127.0.0.1:8000`
- OpenAPI documentation: `http://127.0.0.1:8000/docs`

## 9. Start the dashboard

With the API running in another PowerShell window:

```powershell
python run_dashboard.py
```

If the entry point requires direct Streamlit startup, use:

```powershell
python -m streamlit run dashboard/clearance_queue.py
```

## 10. Typical development order

For a clean local setup, use this order:

1. Activate `.venv`.
2. Install `requirements.txt`.
3. Run `run_data_pipeline.py`.
4. Run `run_knowledge_indexing.py` when the PDF index is missing or outdated.
5. Run `run_model_training.py`.
6. Run `run_database_setup.py`.
7. Run the pytest suite.
8. Start the API and then the dashboard.

## Troubleshooting

- **Module not found:** Confirm that the virtual environment is activated and that the
  current directory is `Project`.
- **Missing processed files:** Run `python run_data_pipeline.py`.
- **Missing model files:** Run `python run_model_training.py`.
- **Missing database records:** Run `python run_database_setup.py`.
- **API authentication failures:** Use one of the seeded accounts defined in
  `config\config.py`; do not place passwords in this document.
- **Model or document downloads fail:** Check network access, then rerun the relevant
  preparation command.
- **Tests use stale artifacts:** Regenerate the data and model artifacts, then rerun the
  test command from the `Project` directory.
