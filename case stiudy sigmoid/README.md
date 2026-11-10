# CycleSight Bike Sharing Demand

CycleSight is a connected demand-planning prototype for the Capital Bikeshare hourly dataset. It combines a FastAPI service that trains and serves a forecast with a Streamlit interface for demand exploration, one statistical hypothesis, fleet planning, and natural-language scenario questions.

## Start the application

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

In a second terminal, from the project root:

```bash
source .venv/bin/activate       # Windows: .venv\Scripts\activate
streamlit run frontend/app.py --server.port 8501
```

Open `http://localhost:8501`. The API docs are at `http://localhost:8000/docs`. The supplied `data/hour.csv` and `data/day.csv` are included. To point at another data directory, set `BIKE_DATA_DIR`; the hourly CSV must be named `hour.csv`.

The API trains the Random Forest at first use and caches it for that process. First model use can take a short time. The model uses only calendar and weather features known for the target hour; `casual`, `registered`, and `cnt` are excluded from the inputs to prevent leakage.

## What is included

- `frontend/app.py` — polished Streamlit dashboard, interactive analysis, fleet simulator, and natural-language explorer.
- `backend/main.py` — FastAPI endpoints, data checks, chronological model evaluation, predictions, hypothesis test, and fleet calculations.
- `data/hour.csv`, `data/day.csv` — supplied UCI Bike Sharing data.
- `docs/architecture.md` — component diagram, data flow, and deployment notes.
- `reports/Bike_Sharing_Demand_Estimation_Report.docx` — case study report informed by the attached reference report.

## API surface

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/health` | API and model status; chronological holdout metrics |
| GET | `/overview` | Quality checks, aggregate summaries, and chart series |
| GET | `/hypothesis` | One-sided Welch test for rush-hour demand |
| POST | `/predict` | Predict rentals for explicit hourly conditions |
| POST | `/fleet` | Forecast plus assumption-based capacity estimate |
| POST | `/ask` | Parse a natural-language scenario and return an estimate |

## Interpretation

The fleet planner estimates concurrent system-wide bikes from hourly rentals, an assumed trip duration, a demand buffer, and a maintenance reserve. These files contain completed, citywide rentals, not station inventories, station locations, trip durations, or denied-rental logs. The estimate cannot identify station shortages or settle the buy-versus-redistribute decision. See the report for the evidence and limitations.
