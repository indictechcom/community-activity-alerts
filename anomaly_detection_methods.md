# Anomaly Detection Approaches for Edit Peaks

This document summarizes and compares the anomaly detection approaches explored for identifying peaks in Wikimedia monthly edit activity data.

## 📌 Objective

To move beyond basic rolling mean thresholds and experiment with advanced anomaly detection methods that offer robustness and interpretability.

##  Methods Evaluated

### 1. STL + Z-score

- **Model**: Seasonal-Trend decomposition using LOESS.
- **Advantages**: Robust to noise, accounts for seasonality.
- **Code**: `find_peaks_stl_z(df, z_thresh=0.5)`
- **Recommendation**: Best performance overall. Balances trend extraction and statistical rigor.

---

### 2. Signal Processing (Prominence-Based)

- **Model**: `scipy.signal.find_peaks` with prominence filtering.
- **Code**: `find_peaks_signal(df, prominence=50000, window=3)`
- **Use Case**: Useful when domain-specific prominence is known. Not robust to baseline drift.

---

### 3. Facebook Prophet + Residual Z-score

- **Model**: Prophet with yearly seasonality; anomaly from residuals.
- **Code**: `find_peaks_prophet(df, z_thresh=1.0)`
- **Pros**: Great interpretability and trend modeling.
- **Cons**: Slightly heavy for small datasets. Requires installation.
- **Note**: Disable weekly/daily seasonality for monthly data.

---


##  Final Notes

- STL+Z is recommended for default usage.

## Location of Code

All code is available in:
- [`polars_migration/`](../polars_migration/)


---

_Last updated: 7 August 2025_
_Author: Aman TS (`Aman2006-code`)_
