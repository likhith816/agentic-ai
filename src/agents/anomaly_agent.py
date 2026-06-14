"""
SteelMind AI Wizard — Anomaly Agent
====================================
Processes uploaded sensor CSV data to detect statistical anomalies, predict
Remaining Useful Life (RUL), and trigger real-time alerts.
"""

import logging
import pandas as pd
import numpy as np
import joblib

from src.schemas import SteelMindState

logger = logging.getLogger(__name__)

ISOLATION_FOREST_PATH = "src/models/isolation_forest.pkl"
RUL_MODEL_PATH = "src/models/rul_model.pkl"
SCALER_PATH = "src/models/scaler.pkl"

SENSOR_COLUMNS = [
    "sensor_temperature",
    "sensor_vibration",
    "sensor_pressure",
    "sensor_rpm",
    "sensor_current"
]

def classify_severity(anomaly_score: float, rul_days: int) -> str:
    """Classify anomaly severity based on score and predicted RUL."""
    if rul_days < 3 or anomaly_score > 0.85:
        return "CRITICAL"
    elif rul_days < 7 or anomaly_score > 0.70:
        return "HIGH"
    elif rul_days < 14 or anomaly_score > 0.60:
        return "MEDIUM"
    else:
        return "LOW"

def find_anomalous_sensor(df: pd.DataFrame, columns: list) -> str:
    """Find the sensor whose latest reading deviates most from its historical mean."""
    deviations = {}
    for col in columns:
        mean_val = df[col].mean()
        std_val = df[col].std()
        latest_val = df[col].iloc[-1]
        
        # Avoid division by zero
        if std_val == 0:
            deviations[col] = 0
        else:
            deviations[col] = abs(latest_val - mean_val) / std_val
            
    return max(deviations, key=deviations.get)

def get_normal_range(sensor_name: str) -> str:
    """Return hardcoded normal ranges for display purposes."""
    ranges = {
        "sensor_temperature": "1150-1300°C",
        "sensor_vibration": "0.5-2.0 mm/s",
        "sensor_pressure": "150-200 bar",
        "sensor_rpm": "1400-1600 RPM",
        "sensor_current": "80-100 A"
    }
    return ranges.get(sensor_name, "Unknown")

def generate_sensor_recommendations(anomaly_score: float, rul_days: int) -> list:
    """Generate recommendations based on severity."""
    recs = []
    if rul_days < 7:
        recs.append("Immediate inspection required: RUL critically low.")
        recs.append("Prepare spare parts for imminent replacement.")
    elif anomaly_score > 0.6:
        recs.append("Monitor sensor readings closely for next 24 hours.")
        recs.append("Schedule proactive maintenance during next available window.")
    else:
        recs.append("Sensor readings within acceptable limits.")
    return recs


# ── Column name aliases — map common CSV headers → internal names ─────────
COLUMN_ALIASES = {
    "sensor_temperature": ["sensor_temperature", "temperature", "temp", "air temperature [k]", "air_temperature"],
    "sensor_vibration":   ["sensor_vibration", "vibration", "vib", "tool wear [min]", "tool_wear"],
    "sensor_pressure":    ["sensor_pressure", "pressure", "torque [nm]", "torque"],
    "sensor_rpm":         ["sensor_rpm", "rpm", "rotational speed [rpm]", "rotational_speed"],
    "sensor_current":     ["sensor_current", "current", "power [w]", "power"],
}


def _resolve_columns(df: pd.DataFrame) -> dict:
    """
    Map DataFrame columns to internal sensor names using aliases.
    Falls back to the first 5 numeric columns if no alias matches.
    Returns dict: {internal_name: actual_column_name}
    """
    cols_lower = {c.lower().strip(): c for c in df.columns}
    resolved = {}

    for internal, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in cols_lower:
                resolved[internal] = cols_lower[alias.lower()]
                break

    # If we resolved < 5, fill in from remaining numeric columns
    if len(resolved) < 5:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        already_used = set(resolved.values())
        for col in numeric_cols:
            if col not in already_used and len(resolved) < 5:
                internal = list(COLUMN_ALIASES.keys())[len(resolved)]
                resolved[internal] = col

    return resolved


def execute_anomaly_check(state: SteelMindState) -> SteelMindState:
    """
    Detect anomalies in sensor CSV using Isolation Forest.
    Predict RUL using XGBoost regression model.

    Accepts any CSV with numeric sensor data — column names are
    resolved via aliases so user-uploaded CSVs don't need exact naming.
    """
    logger.info("📊 Running Anomaly Agent")

    csv_path = state.get("csv_path")
    if not csv_path:
        logger.info("   No CSV path in state — skipping anomaly detection.")
        return state

    logger.info("   CSV path: %s", csv_path)

    try:
        # ── Load & validate CSV ───────────────────────────────
        df = pd.read_csv(csv_path)
        logger.info("   CSV loaded: %d rows × %d cols | columns: %s",
                    len(df), len(df.columns), list(df.columns)[:8])

        if len(df) < 10:
            logger.warning("   CSV has < 10 rows — need more data for prediction.")
            state["anomaly_result"] = {
                "anomaly_detected": False,
                "anomaly_score": 0.0,
                "severity": "LOW",
                "anomalous_sensor": "N/A",
                "current_value": 0.0,
                "normal_range": "N/A",
                "rul_days": 999,
                "rul_confidence": 0.0,
                "alert_triggered": False,
                "trend_data": [],
                "recommendations": ["Upload a CSV with at least 10 rows for anomaly detection."],
            }
            return state

        # ── Resolve column names ──────────────────────────────
        col_map = _resolve_columns(df)
        logger.info("   Column mapping: %s", col_map)

        if len(col_map) < 5:
            logger.warning("   Could not resolve 5 sensor columns. Found: %s", col_map)

        internal_names = list(col_map.keys())
        actual_names   = list(col_map.values())

        # Build feature matrix using resolved columns
        feature_df = df[actual_names].tail(10).copy()
        feature_df.columns = internal_names  # rename to internal for scaler

        # Fill any NaNs with column mean
        feature_df = feature_df.fillna(feature_df.mean())

        # ── Load ML models ────────────────────────────────────
        iso_forest = joblib.load(ISOLATION_FOREST_PATH)
        rul_model  = joblib.load(RUL_MODEL_PATH)
        scaler     = joblib.load(SCALER_PATH)

        # Pad to exactly 5 columns if fewer resolved
        while len(feature_df.columns) < 5:
            feature_df[f"pad_{len(feature_df.columns)}"] = 0.0

        feature_arr = feature_df.values[:, :5]  # ensure exactly 5 features
        scaled = scaler.transform(feature_arr)

        # ── Anomaly detection ─────────────────────────────────
        # decision_function: negative = anomaly, positive = normal
        avg_score = float(np.mean(iso_forest.decision_function(scaled)))
        anomaly_score = max(0.0, min(1.0, 0.5 - (avg_score * 2.0)))

        # ── RUL prediction ────────────────────────────────────
        rul_pred = rul_model.predict(scaled[-1:])
        rul_days = int(max(0, rul_pred[0]))

        # ── Find most anomalous sensor ────────────────────────
        anomalous_internal = find_anomalous_sensor(feature_df, internal_names)
        anomalous_actual   = col_map.get(anomalous_internal, anomalous_internal)
        current_val        = float(df[anomalous_actual].iloc[-1])

        severity        = classify_severity(anomaly_score, rul_days)
        alert_triggered = rul_days < 7

        state["anomaly_result"] = {
            "anomaly_detected": anomaly_score > 0.6,
            "anomaly_score":    round(anomaly_score, 3),
            "severity":         severity,
            "anomalous_sensor": anomalous_internal,
            "current_value":    current_val,
            "normal_range":     get_normal_range(anomalous_internal),
            "rul_days":         rul_days,
            "rul_confidence":   0.85,
            "alert_triggered":  alert_triggered,
            "trend_data":       df[actual_names].tail(30).to_dict("records"),
            "recommendations":  generate_sensor_recommendations(anomaly_score, rul_days),
        }

        if alert_triggered:
            state["force_critical"] = True
            logger.warning("   🚨 CRITICAL ALERT: RUL < 7 days")

        logger.info("   ✅ Anomaly complete | score=%.3f | RUL=%d days | severity=%s",
                    anomaly_score, rul_days, severity)

    except FileNotFoundError:
        logger.error("   ❌ CSV file not found at: %s", csv_path)
    except Exception as e:
        logger.error("   ❌ Anomaly Agent failed: %s", str(e), exc_info=True)

    return state

