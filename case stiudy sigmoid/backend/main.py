from __future__ import annotations

import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("BIKE_DATA_DIR", ROOT / "data"))
FEATURES = ["season", "yr", "mnth", "hr", "holiday", "weekday", "workingday", "weathersit", "temp", "atemp", "hum", "windspeed"]
CATEGORICAL = ["season", "yr", "mnth", "hr", "holiday", "weekday", "workingday", "weathersit"]
NUMERIC = ["temp", "atemp", "hum", "windspeed"]
SEASONS = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
WEATHER = {1: "Clear / partly cloudy", 2: "Mist / cloudy", 3: "Light rain / snow", 4: "Heavy rain / snow"}

app = FastAPI(title="CycleSight Demand API", description="Hourly bike demand forecasting and fleet decision support", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


def load_data(filename: str = "hour.csv") -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"{filename} not found in {DATA_DIR}. Copy the supplied CSV files into the data/ directory.")
    df = pd.read_csv(path, parse_dates=["dteday"])
    df["season_name"] = df.season.map(SEASONS)
    df["weather_name"] = df.weathersit.map(WEATHER)
    df["year_label"] = df.yr.map({0: "2011", 1: "2012"})
    df["temp_c"] = df.temp * 41
    df["rush_hour"] = df.hr.isin([7, 8, 9, 16, 17, 18, 19]).astype(int)
    return df


@lru_cache(maxsize=1)
def model_bundle() -> dict[str, Any]:
    df = load_data()
    # A date-based split keeps the latest 20% of the historical timeline out of training.
    cut = df.dteday.sort_values().drop_duplicates().quantile(0.8)
    train, test = df[df.dteday <= cut], df[df.dteday > cut]
    preprocess = ColumnTransformer([
        ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
        ("numeric", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), NUMERIC),
    ])
    estimator = RandomForestRegressor(n_estimators=180, min_samples_leaf=3, max_features=0.9, random_state=42, n_jobs=-1)
    pipe = Pipeline([("features", preprocess), ("model", estimator)])
    pipe.fit(train[FEATURES], train.cnt)
    predicted = np.maximum(0, pipe.predict(test[FEATURES]))
    metrics = {"r2": round(float(r2_score(test.cnt, predicted)), 3),
               "mae": round(float(mean_absolute_error(test.cnt, predicted)), 1),
               "rmse": round(float(np.sqrt(mean_squared_error(test.cnt, predicted))), 1),
               "train_rows": int(len(train)), "test_rows": int(len(test)),
               "train_through": str(train.dteday.max().date()), "test_from": str(test.dteday.min().date())}
    return {"pipeline": pipe, "metrics": metrics, "data": df}


def conditions_to_row(conditions: dict[str, Any]) -> pd.DataFrame:
    row = {name: conditions[name] for name in FEATURES}
    return pd.DataFrame([row], columns=FEATURES)


def prediction(conditions: dict[str, Any]) -> dict[str, Any]:
    bundle = model_bundle()
    raw = float(bundle["pipeline"].predict(conditions_to_row(conditions))[0])
    return {"predicted_rentals": max(0, int(round(raw))), "model_estimate": round(max(0, raw), 1), "model": "Random Forest", "metrics": bundle["metrics"]}


class PredictionRequest(BaseModel):
    season: int = Field(ge=1, le=4)
    yr: int = Field(ge=0, le=1)
    mnth: int = Field(ge=1, le=12)
    hr: int = Field(ge=0, le=23)
    holiday: int = Field(ge=0, le=1)
    weekday: int = Field(ge=0, le=6)
    workingday: int = Field(ge=0, le=1)
    weathersit: int = Field(ge=1, le=4)
    temp: float = Field(ge=0, le=1)
    atemp: float = Field(ge=0, le=1)
    hum: float = Field(ge=0, le=1)
    windspeed: float = Field(ge=0, le=1)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    season: int = Field(default=3, ge=1, le=4)
    hr: int = Field(default=17, ge=0, le=23)
    workingday: int = Field(default=1, ge=0, le=1)
    weathersit: int = Field(default=1, ge=1, le=4)
    temp_c: float = Field(default=20, ge=-10, le=45)
    hum_pct: float = Field(default=55, ge=0, le=100)
    wind_kmh: float = Field(default=12, ge=0, le=67)
    trip_minutes: int = Field(default=30, ge=5, le=180)
    buffer_pct: int = Field(default=15, ge=0, le=100)
    reserve_pct: int = Field(default=10, ge=0, le=90)


@app.get("/health")
def health() -> dict[str, Any]:
    try:
        bundle = model_bundle()
        return {"status": "ok", "model_ready": True, "rows": len(bundle["data"]), "metrics": bundle["metrics"]}
    except Exception as exc:
        return {"status": "degraded", "model_ready": False, "detail": str(exc)}


@app.get("/overview")
def overview() -> dict[str, Any]:
    df = load_data()
    checks = {"rows": len(df), "columns": 17, "missing_cells": int(df.isna().sum().sum()), "duplicate_rows": int(df.duplicated().sum()),
              "negative_counts": int((df.cnt < 0).sum()), "count_consistency_failures": int((df.cnt != df.casual + df.registered).sum()),
              "date_start": str(df.dteday.min().date()), "date_end": str(df.dteday.max().date()), "weather_4_hours": int((df.weathersit == 4).sum())}
    return {"quality": checks, "headline": {"total_rentals": int(df.cnt.sum()), "mean_hourly": round(float(df.cnt.mean()), 1),
            "peak_hour": int(df.groupby("hr").cnt.mean().idxmax()), "peak_hour_mean": round(float(df.groupby("hr").cnt.mean().max()), 1),
            "p95_hourly": round(float(df.cnt.quantile(.95)), 1), "registered_share_pct": round(float(df.registered.sum()/df.cnt.sum()*100), 1)},
            "hourly": df.groupby(["hr", "workingday"], as_index=False).cnt.mean().rename(columns={"cnt":"mean_rentals"}).to_dict("records"),
            "season": df.groupby("season_name", as_index=False).cnt.mean().rename(columns={"cnt":"mean_rentals"}).to_dict("records"),
            "weather": df.groupby("weather_name", as_index=False).agg(mean_rentals=("cnt","mean"), hours=("cnt","size")).to_dict("records"),
            "daily": df.groupby("dteday", as_index=False).cnt.sum().to_dict("records"),
            "quality_rows": [{"check":"Missing cells","value":checks["missing_cells"]},{"check":"Duplicate rows","value":checks["duplicate_rows"]},
                             {"check":"Negative demand counts","value":checks["negative_counts"]},{"check":"Count identity failures","value":checks["count_consistency_failures"]}]}


@app.post("/predict")
def predict(request: PredictionRequest) -> dict[str, Any]:
    return prediction(request.model_dump())


@app.get("/hypothesis")
def hypothesis() -> dict[str, Any]:
    """One-sided Welch test of rush-hour demand > other hours."""
    df = load_data()
    rush = df.loc[df.rush_hour == 1, "cnt"].to_numpy(dtype=float)
    other = df.loc[df.rush_hour == 0, "cnt"].to_numpy(dtype=float)
    v1, v2 = rush.var(ddof=1), other.var(ddof=1)
    se = math.sqrt(v1/len(rush) + v2/len(other))
    t = (rush.mean() - other.mean()) / se
    p = 0.5 * math.erfc(t / math.sqrt(2))  # Large-sample one-sided approximation.
    pooled = math.sqrt(((len(rush)-1)*v1+(len(other)-1)*v2)/(len(rush)+len(other)-2))
    d = (rush.mean()-other.mean())/pooled
    return {"null": "Mean hourly rentals in rush hours are no higher than in other hours.",
            "alternative": "Mean hourly rentals are higher during 07:00–09:00 and 16:00–19:00.",
            "test": "Welch two-sample t-test, one-sided; large-sample normal approximation for p-value", "alpha": 0.05,
            "statistic_t": round(float(t), 2), "p_value": float(p), "effect_size_cohens_d": round(float(d), 3),
            "p_value_text": f"p < 1e-16" if p < 1e-16 else f"p = {p:.3g}",
            "rush": {"n":len(rush),"mean":round(float(rush.mean()),1),"median":float(np.median(rush))},
            "other": {"n":len(other),"mean":round(float(other.mean()),1),"median":float(np.median(other))},
            "decision": "Reject the null hypothesis" if p < .05 else "Do not reject the null hypothesis",
            "note": "Hours are temporally related; interpret the p-value as descriptive evidence, not a causal claim."}


@app.post("/fleet")
def fleet(request: PredictionRequest, trip_minutes: int = 30, buffer_pct: int = 15, reserve_pct: int = 10) -> dict[str, Any]:
    if not 5 <= trip_minutes <= 180 or not 0 <= buffer_pct <= 100 or not 0 <= reserve_pct <= 90:
        raise HTTPException(422, "Trip time, buffer, or reserve is outside the supported range.")
    pred = prediction(request.model_dump())
    buffered = pred["model_estimate"] * (1 + buffer_pct/100)
    gross = buffered * trip_minutes / 60
    requirement = math.ceil(gross / (1-reserve_pct/100))
    return {**pred, "assumptions": {"trip_minutes":trip_minutes,"buffer_pct":buffer_pct,"reserve_pct":reserve_pct},
            "buffered_rentals_per_hour":round(buffered,1), "estimated_concurrent_bikes":math.ceil(gross), "planning_fleet":requirement,
            "formula":"ceil(predicted hourly rentals × (1 + demand buffer) × trip duration in hours ÷ (1 − reserve share))",
            "caveat":"A system-wide concurrency estimate. Trip duration is assumed; it is not present in these files. It cannot size individual stations or reveal denied rentals."}


def parse_question(q: str, defaults: AskRequest) -> dict[str, int]:
    text = q.lower()
    result = {"season":defaults.season,"hr":defaults.hr,"workingday":defaults.workingday,"weathersit":defaults.weathersit,"mnth":6 if defaults.season==2 else 9 if defaults.season==3 else 12 if defaults.season==4 else 3,"weekday":2,"yr":1,"holiday":0}
    for word, val in [("spring",1),("summer",2),("fall",3),("autumn",3),("winter",4)]:
        if word in text: result["season"] = val
    if any(w in text for w in ["weekend","non-working","non working"]): result["workingday"] = 0
    if any(w in text for w in ["working day","weekday","workday"]): result["workingday"] = 1
    for key, val, words in [(1,1,["clear","sunny"]),(2,2,["mist","cloudy"]),(3,3,["rain","snow"]),(4,4,["heavy rain","storm"] )]:
        if any(w in text for w in words): result["weathersit"] = val
    if "heavy rain" in text or "heavy snow" in text or "storm" in text: result["weathersit"] = 4
    match = re.search(r"\b(1[0-2]|[1-9])\s*(am|pm)\b", text)
    if match:
        hour=int(match.group(1))%12 + (12 if match.group(2)=="pm" else 0)
        result["hr"] = hour
    else:
        match = re.search(r"\b(?:at\s*)?(\d{1,2}):?00\b", text)
        if match and int(match.group(1))<=23: result["hr"] = int(match.group(1))
    if "2011" in text: result["yr"],result["mnth"] = 0,1
    temp = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:°?c|celsius)\b", text)
    if temp: result["temp"] = min(1,max(0,float(temp.group(1))/41))
    else: result["temp"] = min(1,max(0,20/41))
    result["atemp"] = min(1,max(0,(result["temp"]*41)/50))
    result["hum"] = defaults.hum_pct/100
    result["windspeed"] = defaults.wind_kmh/67
    return result


@app.post("/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    conditions = parse_question(request.question, request)
    pred = prediction(conditions)
    trip = request.trip_minutes
    buffered = pred["model_estimate"]*(1+request.buffer_pct/100)
    fleet_size = math.ceil(buffered*trip/60/(1-request.reserve_pct/100))
    day_type = "working day" if conditions["workingday"] else "non-working day"
    season = SEASONS[conditions["season"]]
    answer = (f"For a {season.lower()} {day_type} at {conditions['hr']:02d}:00 in {WEATHER[conditions['weathersit']].lower()} conditions, "
              f"the model estimates about {pred['predicted_rentals']} rentals in the hour. Under your {trip}-minute trip, "
              f"{request.buffer_pct}% buffer, and {request.reserve_pct}% reserve assumptions, the rough system-wide planning figure is {fleet_size} bikes.")
    return {"answer":answer,"interpreted_conditions":conditions,"prediction":pred,"planning_fleet":fleet_size,
            "disclaimer":"This is an aggregate hourly estimate. It does not identify station-level shortages or unmet demand."}
