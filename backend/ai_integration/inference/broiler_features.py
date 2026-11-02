"""
Feature engineering for the broiler price forecast model.

Ported directly from the `broiler_forecast_api` package that shipped
with the trained model artifacts (itself ported 1:1 from the research
notebook), so inference produces features identically to how the model
was trained. Do not change the feature formulas here without retraining
`lstm_model_28.keras` / `xgboost_clf.json` to match.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from hijridate import Hijri

TARGET = "lhr_farm"
LOOKBACK = 28

EXOG_COLS = ["ramadan_proximity", "eid_fitr_proximity", "eid_adha_proximity",
             "monsoon_flood_score", "ndv_seasonal_risk"]

FX_COLS = ["usdpkr", "usdpkr_lag1", "usdpkr_chg1", "usdpkr_chg7", "usdpkr_roll7"]

LAG_COLS = ["lag_1", "lag_2", "lag_3", "lag_7",
            "roll_mean_7", "roll_mean_14", "roll_std_7",
            "diff_1", "dow", "month", "open_close_spread",
            "roc_3", "roc_5", "roc_10", "lstm_implied_chg"]

FEED_COLS = ["feed_price_50kg", "feed_chg1m", "feed_chg3m", "feed_roll3m"]

TA_COLS = ["ema9", "ema21", "ema_cross", "rsi14",
           "macd", "macd_signal", "macd_hist",
           "vol7", "vol14", "vol21", "atr7"]

ALL_FEATS = LAG_COLS + EXOG_COLS + FX_COLS + FEED_COLS + TA_COLS

NDV_RISK = {1: 0.80, 2: 0.80, 3: 0.45, 4: 0.30, 5: 0.35,
            6: 0.80, 7: 0.80, 8: 0.50, 9: 0.40, 10: 0.30, 11: 0.30, 12: 0.55}

FLOOD_SEVERITY = {
    (2022, 7, 9): 1.00, (2023, 7, 7): 0.55, (2025, 8, 9): 0.70,
}


def _to_date(d):
    return d.date() if hasattr(d, "date") else d


def build_hijri_events(hy_start=1438, hy_end=1452):
    events = {"ramadan_start": [], "ramadan_end": [], "eid_fitr": [], "eid_adha": []}
    for hy in range(hy_start, hy_end + 1):
        try:
            rs = Hijri(hy, 9, 1).to_gregorian()
            sw = Hijri(hy, 10, 1).to_gregorian()
            re = sw - timedelta(days=1)
            ea = Hijri(hy, 12, 10).to_gregorian()
            events["ramadan_start"].append(date(rs.year, rs.month, rs.day))
            events["ramadan_end"].append(date(re.year, re.month, re.day))
            events["eid_fitr"].append(date(sw.year, sw.month, sw.day))
            events["eid_adha"].append(date(ea.year, ea.month, ea.day))
        except Exception:
            pass
    return events


def proximity_score(d, event_dates, window=7):
    if not event_dates:
        return 0.0
    d = _to_date(d)
    delta = min(abs((d - ed).days) for ed in event_dates)
    return round(max(0.0, 1 - delta / window), 4)


def in_range(d, starts, ends):
    d = _to_date(d)
    return int(any(s <= d <= e for s, e in zip(starts, ends)))


def monsoon_score(d, historical=True):
    d = _to_date(d)
    peak, width = 225, 75
    base = max(0.0, round((1 - abs(d.timetuple().tm_yday - peak) / width) * 0.45, 4))
    if historical:
        for (yr, ms, me), sev in FLOOD_SEVERITY.items():
            if d.year == yr and ms <= d.month <= me:
                return round(max(base, sev), 4)
    return base


def future_exog(target_date, events):
    d = target_date.date() if hasattr(target_date, "date") else target_date
    return {
        "is_ramadan": in_range(d, events["ramadan_start"], events["ramadan_end"]),
        "ramadan_proximity": max(proximity_score(d, events["ramadan_start"]),
                                  proximity_score(d, events["ramadan_end"])),
        "eid_fitr_proximity": proximity_score(d, events["eid_fitr"]),
        "eid_adha_proximity": proximity_score(d, events["eid_adha"]),
        "monsoon_flood_score": monsoon_score(d, historical=False),
        "ndv_seasonal_risk": NDV_RISK[d.month],
    }


def add_exog_features(df, historical=True):
    """Training-time version of the calendar/seasonal features — adds
    them as full columns on a whole history dataframe. (The inference-
    time equivalent, `future_exog`, computes the same features for a
    single future date instead.) Matches the training notebook's
    `add_exog_features` cell exactly."""
    df = df.copy()
    df["_date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    events = build_hijri_events()
    df["is_ramadan"] = df["_date"].dt.date.apply(
        lambda d: in_range(d, events["ramadan_start"], events["ramadan_end"]))
    df["ramadan_proximity"] = df["_date"].dt.date.apply(
        lambda d: max(proximity_score(d, events["ramadan_start"]),
                      proximity_score(d, events["ramadan_end"])))
    df["eid_fitr_proximity"] = df["_date"].dt.date.apply(
        lambda d: proximity_score(d, events["eid_fitr"]))
    df["eid_adha_proximity"] = df["_date"].dt.date.apply(
        lambda d: proximity_score(d, events["eid_adha"]))
    df["monsoon_flood_score"] = df["_date"].dt.date.apply(
        lambda d: monsoon_score(d, historical=historical))
    df["ndv_seasonal_risk"] = df["_date"].dt.month.map(NDV_RISK)
    return df


def compute_ta(df, col=TARGET):
    """Training-time technical indicators (RSI/MACD/EMA/volatility)
    computed properly over the full price history with pandas
    .ewm()/.rolling() — the real formulas, not the rolling-window
    approximation `compute_live_ta` uses for one-step inference."""
    c = df[col].copy()
    df["ema9"] = c.ewm(span=9, adjust=False).mean()
    df["ema21"] = c.ewm(span=21, adjust=False).mean()
    df["ema_cross"] = df["ema9"] - df["ema21"]
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi14"] = 100 - (100 / (1 + rs))
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    ret = c.pct_change()
    df["vol7"] = ret.rolling(7).std()
    df["vol14"] = ret.rolling(14).std()
    df["vol21"] = ret.rolling(21).std()
    df["atr7"] = (df["lhr_open"] - df["lhr_close"]).abs().rolling(7).mean()
    return df


def prepare_dataset(df_raw):
    """Full training-time feature pipeline: raw source CSV -> fully
    engineered feature dataframe (same shape/columns as
    `prepared_history.csv`). Matches the training notebook's
    `prepare_dataset` cell exactly — this is what turns a freshly
    extended source CSV into a fresh `prepared_history.csv` for
    retraining."""
    df = df_raw.copy()
    df["_date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    df = df.sort_values("_date").reset_index(drop=True)
    for col in ["lhr_open", "lhr_close", "egg_per_30doz", "lhr_doc", "usdpkr", "feed_price_50kg"]:
        if col in df.columns:
            df[col] = df[col].ffill().bfill()
    df = add_exog_features(df, historical=True)
    if "usdpkr" in df.columns:
        df["usdpkr_lag1"] = df["usdpkr"].shift(1)
        df["usdpkr_chg1"] = df["usdpkr"].diff(1)
        df["usdpkr_chg7"] = df["usdpkr"].diff(7)
        df["usdpkr_roll7"] = df["usdpkr"].shift(1).rolling(7).mean()
    else:
        for c in FX_COLS:
            df[c] = 280.0
    if "feed_price_50kg" in df.columns:
        df["feed_chg1m"] = df["feed_price_50kg"].diff(30)
        df["feed_chg3m"] = df["feed_price_50kg"].diff(90)
        df["feed_roll3m"] = df["feed_price_50kg"].rolling(90).mean()
    else:
        for c in FEED_COLS:
            df[c] = 6000.0
    for lag in [1, 2, 3, 7]:
        df[f"lag_{lag}"] = df[TARGET].shift(lag)
    df["roll_mean_7"] = df[TARGET].shift(1).rolling(7).mean()
    df["roll_mean_14"] = df[TARGET].shift(1).rolling(14).mean()
    df["roll_std_7"] = df[TARGET].shift(1).rolling(7).std()
    df["diff_1"] = df[TARGET].diff(1)
    df["dow"] = df["_date"].dt.dayofweek
    df["month"] = df["_date"].dt.month
    df["open_close_spread"] = df["lhr_open"] - df["lhr_close"]
    df["roc_3"] = df[TARGET].pct_change(3)
    df["roc_5"] = df[TARGET].pct_change(5)
    df["roc_10"] = df[TARGET].pct_change(10)
    df = compute_ta(df, TARGET)
    return df


def rolling_ema(prices, span):
    alpha, ema = 2 / (span + 1), prices[0]
    for p in prices[1:]:
        ema = alpha * p + (1 - alpha) * ema
    return ema


def compute_live_ta(window, oc_win, oc_recent):
    """Compute TA features from a rolling price window (inference mode)."""
    arr = np.array(window)
    n = len(arr)
    ema9 = rolling_ema(arr[-min(n, 50):], 9)
    ema21 = rolling_ema(arr[-min(n, 50):], 21)
    diffs = np.diff(arr[-15:]) if n >= 15 else np.array([0])
    gains = diffs.clip(min=0)
    losses = (-diffs).clip(min=0)
    avg_g = gains.mean() if len(gains) else 0
    avg_l = losses.mean() if len(losses) else 1e-9
    rsi = 100 - (100 / (1 + (avg_g / (avg_l if avg_l > 0 else 1e-9))))
    ema12 = rolling_ema(arr[-min(n, 50):], 12)
    ema26 = rolling_ema(arr[-min(n, 50):], 26)
    macd = ema12 - ema26
    macd_sig = macd * 0.85
    macd_hist = macd - macd_sig
    rets = np.diff(arr) / arr[:-1]
    vol7 = rets[-7:].std() if len(rets) >= 7 else 0
    vol14 = rets[-14:].std() if len(rets) >= 14 else 0
    vol21 = rets[-21:].std() if len(rets) >= 21 else 0
    atr7 = np.mean(oc_win[-7:]) if len(oc_win) >= 7 else oc_recent
    return {
        "ema9": ema9, "ema21": ema21, "ema_cross": ema9 - ema21,
        "rsi14": rsi,
        "macd": macd, "macd_signal": macd_sig, "macd_hist": macd_hist,
        "vol7": vol7, "vol14": vol14, "vol21": vol21,
        "atr7": atr7,
    }
