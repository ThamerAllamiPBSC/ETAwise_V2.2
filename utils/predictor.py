"""Shared ETAwise freight prediction engine for all three Streamlit portals.

Input: branch ID and destination metro. Output: historical county-to-county
median truck travel time estimate, NOT doorstep package delivery ETA.
"""
from functools import lru_cache
from pathlib import Path
import math

import joblib
import numpy as np
import pandas as pd

try:
    from .locations import get_route
except ImportError:  # supports running directly from utils directory
    from locations import get_route

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "etawise_bts_model_bundle.joblib"

@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"Place the downloaded BTS bundle at: {MODEL_PATH}")
    bundle = joblib.load(MODEL_PATH)  # load only trusted files
    if not isinstance(bundle, dict):
        raise TypeError("Expected a dictionary model bundle")
    for key in ("features", "selected_name", "target_unit"):
        if key not in bundle:
            raise KeyError(f"Model bundle missing {key!r}")
    if bundle["target_unit"] != "hours":
        raise ValueError("This predictor expects a model trained to predict hours")
    return bundle


def make_features(route: dict, expected_features: list[str]) -> pd.DataFrame:
    distance = float(route["straight_km"])
    if not math.isfinite(distance) or distance < 0:
        raise ValueError("Invalid route distance")
    origin_lat, origin_lon = route["origin_lat"], route["origin_lon"]
    destination_lat, destination_lon = route["destination_lat"], route["destination_lon"]
    values = {
        "straight_km": distance,
        "log1p_straight_km": math.log1p(distance),
        "origin_lat": origin_lat,
        "origin_lon": origin_lon,
        "destination_lat": destination_lat,
        "destination_lon": destination_lon,
        "abs_lat_change": abs(destination_lat - origin_lat),
        "abs_lon_change": abs(destination_lon - origin_lon),
        "midpoint_lat": (origin_lat + destination_lat) / 2,
        "midpoint_lon": (origin_lon + destination_lon) / 2,
    }
    missing = set(expected_features) - set(values)
    if missing:
        raise ValueError(f"Unsupported model features: {sorted(missing)}")
    return pd.DataFrame([{name: values[name] for name in expected_features}], columns=expected_features)


def predict_delivery_time(origin_branch: str, destination_metro: str) -> dict:
    """Return prediction plus metadata for Consumer, Trucker, and Admin.

    Same-county routes have zero county-centroid distance. These cannot be
    meaningfully estimated with the county-to-county freight model.
    """
    route = get_route(origin_branch, destination_metro)
    if route["origin_county"] == route["destination_county"]:
        return {**route, "estimated_hours": None, "estimated_minutes": None,
                "display_time": "Local route — county model not applicable",
                "status": "same_county_unsupported"}

    bundle = load_model()
    frame = make_features(route, list(bundle["features"]))
    selected = bundle["selected_name"].strip().lower()
    if "residual" in selected:
        trend = bundle["distance_trend"].predict(frame[["straight_km"]])
        correction = bundle["residual_forest"].predict(frame)
        prediction = float(np.maximum(0, trend + correction)[0])
    elif "random forest" in selected:
        prediction = float(bundle["random_forest_model"].predict(frame)[0])
    elif "linear" in selected:
        prediction = float(bundle["linear_model"].predict(frame)[0])
    else:
        raise ValueError(f"Unrecognized selected model: {bundle['selected_name']!r}")
    if not math.isfinite(prediction):
        raise ValueError("Model returned a non-finite prediction")
    prediction = max(0.0, prediction)
    total_minutes = round(prediction * 60)
    days, remainder = divmod(total_minutes, 1440)
    hours, minutes = divmod(remainder, 60)
    parts = ([f"{days}d"] if days else []) + [f"{hours}h", f"{minutes}m"]
    return {**route, "estimated_hours": round(prediction, 2),
            "estimated_minutes": total_minutes, "display_time": " ".join(parts),
            "status": "ok", "model_name": bundle["selected_name"]}


if __name__ == "__main__":
    for branch in ("QS-01", "QS-05", "QS-10"):
        print(predict_delivery_time(branch, "Orlando"))
