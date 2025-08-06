import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from scipy.signal import find_peaks
from prophet import Prophet

def find_peaks_stl_z(df, z_thresh=0.5):
    df = df.sort_values("timestamp").reset_index(drop=True)

    if len(df) < 24:
        return []  # STL needs at least 2 seasonal cycles (assuming 12-month seasonality)

    # Assume monthly data: period = 12
    stl = STL(df["edit_count"], period=12, robust=True)
    result = stl.fit()

    trend = result.trend
    resid = result.resid

    # Z-score of residual
    resid_mean = np.mean(resid)
    resid_std = np.std(resid)
    z_scores = (resid - resid_mean) / resid_std

    peaks = []
    for i, z in enumerate(z_scores):
        if z > z_thresh:
            peaks.append({
                "timestamp": df.at[i, "timestamp"],
                "edit_count": df.at[i, "edit_count"],
                "rolling_mean": trend[i],   # "trend" should be the key instead of rolling_mean
                "threshold": trend[i] + z_thresh * resid_std,
                "percentage_difference": ((df.at[i, "edit_count"] - trend[i]) / trend[i]) * 100,# "percentage_above_trend" should be the key instead of percentage_difference
            })
    return peaks

def find_peaks_signal(df, prominence=50000, window=3):
    df = df.sort_values("timestamp").reset_index(drop=True)

    if len(df) < window:
        return []

    # Smooth the data a bit (optional, just like STL did)
    df["rolling_mean"] = df["edit_count"].rolling(window=window, center=True).mean()

    # Use rolling mean for peak detection
    peaks_indices, properties = find_peaks(df["rolling_mean"], prominence=prominence)

    peaks = []
    for i in peaks_indices:
        baseline = df.at[i, "rolling_mean"]
        edit_count = df.at[i, "edit_count"]
        if baseline == 0 or np.isnan(baseline):
            continue  # avoid divide-by-zero or NaN
        peaks.append({
            "timestamp": df.at[i, "timestamp"],
            "edit_count": edit_count,
            "rolling_mean": baseline,
            "threshold": baseline + prominence, # "prominance_threshold" should be the key instead of threshold
            "percentage_difference": ((edit_count - baseline) / baseline) * 100, # "percentage_above_baseline" should be the key instead of percentage_difference
        })

    return peaks

def find_peaks_prophet(df, z_thresh=1.0):
    df = df.sort_values("timestamp").reset_index(drop=True)

    if len(df) < 24:
        return []  # Prophet needs reasonable history

    # Prepare data for Prophet
    prophet_df = df[["timestamp", "edit_count"]].rename(columns={"timestamp": "ds", "edit_count": "y"})

    # Remove timezone info if present
    prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)

    model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=True)
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=0)
    forecast = model.predict(future)

    # Use trend as baseline
    trend = forecast["trend"]
    yhat = forecast["yhat"]
    resid = prophet_df["y"] - yhat

    resid_mean = resid.mean()
    resid_std = resid.std()
    z_scores = (resid - resid_mean) / resid_std

    peaks = []
    for i, z in enumerate(z_scores):
        if z > z_thresh:
            base = trend[i]
            observed = prophet_df.at[i, "y"]
            if base == 0 or np.isnan(base):
                continue
            peaks.append({
                "timestamp": prophet_df.at[i, "ds"],
                "edit_count": observed,
                "rolling_mean": base, # "trend" should be the key instead of rolling_mean
                "threshold": base + z_thresh * resid_std,
                "percentage_difference": ((observed - base) / base) * 100, # "percentage_above_threshold" should be the key instead of percentage_difference
            })

    return peaks
