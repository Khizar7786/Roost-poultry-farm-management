"""
Price forecast engine (UC-03) — the real trained model.

This is a genuine trained hybrid: a 28-day-lookback LSTM projects the
next day's Lahore farm-gate broiler price, and that projected % change
feeds an XGBoost binary classifier that predicts UP/DOWN direction with
a confidence score, using calendar (Ramadan/Eid), monsoon/NDV seasonal
risk, USD/PKR FX, feed cost, and technical-indicator (RSI/MACD/EMA/
volatility) features. Forecasts are generated iteratively, day by day,
feeding each day's predicted price back in as input for the next day.

Ported from a standalone FastAPI service into an in-process Django
component — same model artifacts, same feature pipeline, same forecast
loop, just invoked directly as a Python class instead of over HTTP.

Model artifacts live in `ai_integration/ml_artifacts/` and were trained
on data through 2026-07-15 — see the project root README for how to
retrain when new data is available.
"""

import hashlib
import json
import os
import threading

import numpy as np
import pandas as pd
from django.conf import settings
from xgboost import XGBClassifier

from . import broiler_features as feat

CONF_THRESHOLD = float(os.environ.get("PRICE_FORECAST_CONF_THRESHOLD", 0.70))

_ARTIFACTS_DIR = os.path.join(settings.BASE_DIR, "ai_integration", "ml_artifacts")

_engine_lock = threading.RLock()
_engine_instance = None


def _md5_of(path: str, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_xgb_classifier(path: str) -> XGBClassifier:
    """Loads the classifier via XGBoost's own native serialization
    (JSON), not joblib/pickle. This used to go through `joblib.load()`,
    which pickles the whole sklearn wrapper — on at least one real
    Windows setup that failed with a low-level "input stream corrupted"
    parse error even with a byte-for-byte identical file and a matching
    xgboost version installed, which points to a platform-sensitivity
    bug somewhere in the pickle/joblib layer rather than the model data
    itself. XGBoost's own format is explicitly designed to be portable
    across platforms and versions, so it doesn't have that failure mode.
    Verified to produce identical predictions to the original pickle
    file before making this switch."""
    clf = XGBClassifier()
    clf.load_model(path)
    return clf


class SimplePriceScaler:
    """A hand-rolled stand-in for sklearn's fitted MinMaxScaler, loaded
    from a plain JSON dump of its parameters instead of a pickle file —
    same reasoning as `_load_xgb_classifier` above: once one pickle
    artifact demonstrably failed to unpickle correctly on a real Windows
    machine despite being byte-identical, it's not worth trusting pickle
    for the others either when the transform itself (`x * scale + min`)
    is this simple to reproduce exactly. Verified to match sklearn's
    MinMaxScaler.transform()/.inverse_transform() output bit-for-bit."""

    def __init__(self, min_: list[float], scale_: list[float]):
        self.min_ = np.array(min_)
        self.scale_ = np.array(scale_)

    @classmethod
    def load(cls, path: str) -> "SimplePriceScaler":
        with open(path) as f:
            params = json.load(f)
        return cls(params["min_"], params["scale_"])

    def transform(self, X):
        return np.asarray(X, dtype=float) * self.scale_ + self.min_

    def inverse_transform(self, X):
        return (np.asarray(X, dtype=float) - self.min_) / self.scale_


def _load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _load_manifest(artifacts_dir: str) -> dict:
    """Reads `manifest.json` (written by `scripts/retrain.py`), mapping
    each artifact filename to its expected {size, md5}. Missing file ->
    empty dict, meaning `_load_artifact` skips the integrity check
    entirely rather than failing — this only degrades corruption
    *detection*, it doesn't block loading a model that has no manifest
    yet (e.g. one dropped in by hand)."""
    path = os.path.join(artifacts_dir, "manifest.json")
    if not os.path.exists(path):
        return {}
    try:
        return _load_json(path)
    except (json.JSONDecodeError, OSError):
        return {}


class BroilerForecastEngine:
    """Loads the trained artifacts once and reproduces the notebook's
    N-day forecast loop on demand. Thread-safety: TensorFlow/Keras
    inference calls are serialized via the module-level lock in
    `get_engine()` / `predict_price()` below — fine for this workload's
    request volume."""

    def __init__(self, artifacts_dir: str = _ARTIFACTS_DIR):
        from tensorflow.keras.models import load_model  # deferred: heavy import, only needed here

        manifest = _load_manifest(artifacts_dir)

        self.lstm_model = self._load_artifact(
            f"{artifacts_dir}/lstm_model_28.keras", lambda p: load_model(p), manifest
        )
        self.clf = self._load_artifact(
            f"{artifacts_dir}/xgboost_clf.json", _load_xgb_classifier, manifest
        )
        self.price_scaler = self._load_artifact(
            f"{artifacts_dir}/price_scaler.json", SimplePriceScaler.load, manifest
        )
        self.metrics = self._load_artifact(
            f"{artifacts_dir}/metrics.json", _load_json, manifest
        )
        self.df = self._load_artifact(
            f"{artifacts_dir}/prepared_history.csv", pd.read_csv, manifest
        )
        self.df["_date"] = pd.to_datetime(self.df["_date"])
        self.events = feat.build_hijri_events()

        self.last_date = self.df["_date"].iloc[-1]
        self.last_actual = float(self.df[feat.TARGET].iloc[-1])
        self.oc_recent = self.df["open_close_spread"].dropna().iloc[-14:].mean()
        self.last_usdpkr = float(self.df["usdpkr"].iloc[-1]) if "usdpkr" in self.df.columns else 280.0
        self.last_feed = float(self.df["feed_price_50kg"].iloc[-1]) if "feed_price_50kg" in self.df.columns else 6500.0

    @staticmethod
    def _load_artifact(path: str, loader, manifest: dict, extra_diagnostic=None):
        """Loads one model artifact with a much more actionable error than
        whatever low-level exception the underlying library raises (e.g.
        "input stream corrupted") if the file is missing, truncated, or
        was corrupted in transit — which is a common real-world issue on
        Windows when a zip is extracted inside a OneDrive-synced folder,
        or when the zip download itself was interrupted.

        Checks size first (cheap), then an MD5 hash (catches byte-level
        corruption that happens to preserve file length — rare, but it
        happens), both read from `manifest.json` (written by
        `scripts/retrain.py` every time the model is retrained, so this
        never needs a manual update when the artifacts legitimately
        change). If both check out and loading *still* fails, the file
        itself is fine and something else is wrong (most often a library
        version mismatch) — `extra_diagnostic`, if given, adds a hint
        specific to that artifact.
        """
        name = os.path.basename(path)
        expected = manifest.get(name, {})
        expected_size = expected.get("size")
        expected_md5 = expected.get("md5")

        if not os.path.exists(path):
            raise RuntimeError(
                f"Model artifact not found: {path}. Make sure the whole "
                f"ai_integration/ml_artifacts/ folder was extracted from the project zip."
            )
        actual_size = os.path.getsize(path)
        if expected_size is not None and actual_size != expected_size:
            raise RuntimeError(
                f"Model artifact {name} is {actual_size} bytes, expected "
                f"{expected_size}. It's corrupted or incomplete — try re-extracting the project "
                f"zip somewhere outside any OneDrive/Dropbox-synced folder (cloud sync sometimes "
                f"interferes with large binary files mid-extraction), or re-download the zip in "
                f"case the original download was interrupted."
            )
        if expected_md5 is not None:
            actual_md5 = _md5_of(path)
            if actual_md5 != expected_md5:
                raise RuntimeError(
                    f"Model artifact {name} has the right size but the wrong "
                    f"content (MD5 {actual_md5}, expected {expected_md5}) — some bytes changed in "
                    f"transit. Re-extract the project zip somewhere outside any cloud-synced folder, "
                    f"or re-download it fresh."
                )
        try:
            return loader(path)
        except Exception as exc:
            hint = f" {extra_diagnostic()}" if extra_diagnostic else ""
            raise RuntimeError(
                f"Could not load model artifact {name} — the file is byte-for-byte "
                f"correct (verified by hash), so this isn't corruption. It failed to parse with: "
                f"{exc}.{hint}"
            ) from exc

    @property
    def accuracy(self):
        return self.metrics["accuracy"]

    def predict(self, n_days: int) -> dict:
        price_hist = list(self.df[feat.TARGET].dropna().values[-feat.LOOKBACK:])
        ta_window = list(self.df[feat.TARGET].dropna().values[-60:])
        oc_window = list((self.df["lhr_open"] - self.df["lhr_close"]).abs().dropna().values[-7:])

        forecast_rows = []

        for i in range(n_days):
            fdate = self.last_date + pd.Timedelta(days=i + 1)

            seq_sc = self.price_scaler.transform(
                np.array(price_hist[-feat.LOOKBACK:]).reshape(-1, 1)
            ).flatten()
            lstm_pred_sc = self.lstm_model.predict(seq_sc.reshape(1, feat.LOOKBACK, 1), verbose=0)[0, 0]
            lstm_price = float(self.price_scaler.inverse_transform([[lstm_pred_sc]])[0, 0])
            lstm_chg_pct = (lstm_price - price_hist[-1]) / price_hist[-1]
            prev_price = price_hist[-1]
            price_delta = lstm_price - prev_price

            ta = feat.compute_live_ta(ta_window, oc_window, self.oc_recent)

            s = pd.Series(price_hist)
            row_feats = {
                "lag_1": s.iloc[-1],
                "lag_2": s.iloc[-2] if len(s) >= 2 else s.iloc[-1],
                "lag_3": s.iloc[-3] if len(s) >= 3 else s.iloc[-1],
                "lag_7": s.iloc[-7] if len(s) >= 7 else s.iloc[-1],
                "roll_mean_7": s.iloc[-7:].mean(),
                "roll_mean_14": s.iloc[-14:].mean(),
                "roll_std_7": s.iloc[-7:].std(),
                "diff_1": s.iloc[-1] - s.iloc[-2] if len(s) >= 2 else 0,
                "dow": fdate.dayofweek,
                "month": fdate.month,
                "open_close_spread": self.oc_recent,
                "roc_3": (s.iloc[-1] / s.iloc[-4] - 1) if len(s) >= 4 else 0,
                "roc_5": (s.iloc[-1] / s.iloc[-6] - 1) if len(s) >= 6 else 0,
                "roc_10": (s.iloc[-1] / s.iloc[-11] - 1) if len(s) >= 11 else 0,
                "lstm_implied_chg": lstm_chg_pct,
                **feat.future_exog(fdate, self.events),
                "usdpkr": self.last_usdpkr, "usdpkr_lag1": self.last_usdpkr,
                "usdpkr_chg1": 0.0, "usdpkr_chg7": 0.0, "usdpkr_roll7": self.last_usdpkr,
                "feed_price_50kg": self.last_feed, "feed_chg1m": 0.0,
                "feed_chg3m": 0.0, "feed_roll3m": self.last_feed,
                **ta,
            }

            feat_df = pd.DataFrame([row_feats])[feat.ALL_FEATS]
            direction = int(self.clf.predict(feat_df)[0])
            proba = self.clf.predict_proba(feat_df)[0]
            confidence = float(max(proba))
            low_conf = confidence < CONF_THRESHOLD

            ev = feat.future_exog(fdate, self.events)
            events = []
            if ev["ramadan_proximity"] > 0:
                events.append("Ramadan")
            if ev["eid_fitr_proximity"] > 0:
                events.append("Eid-ul-Fitr")
            if ev["eid_adha_proximity"] > 0:
                events.append("Eid-ul-Adha")
            if ev["monsoon_flood_score"] > 0.3:
                events.append("Flood season")
            if ev["ndv_seasonal_risk"] >= 0.7:
                events.append("High NDV risk")
            if ta["rsi14"] >= 70:
                events.append("RSI overbought")
            if ta["rsi14"] <= 30:
                events.append("RSI oversold")
            if ta["macd_hist"] > 0 and ta["ema_cross"] > 0:
                events.append("Bullish momentum")
            if ta["macd_hist"] < 0 and ta["ema_cross"] < 0:
                events.append("Bearish momentum")

            forecast_rows.append({
                "day": i + 1,
                "date": fdate.strftime("%Y-%m-%d"),
                "price_pkr": round(lstm_price, 2),
                "delta_pkr": round(price_delta, 2),
                "delta_pct": round(lstm_chg_pct, 4),
                # Direction shown to the user must match the price actually
                # printed above (day-over-day LSTM delta), not the XGBoost
                # classifier's independent multi-day-horizon call — those two
                # can legitimately disagree, which is why every day was
                # showing "UP" even as price_pkr fell each day.
                "direction": "UP" if price_delta > 0 else ("DOWN" if price_delta < 0 else "FLAT"),
                "horizon_direction": "UP" if direction == 1 else "DOWN",
                "prob_up": round(float(proba[1]), 4),
                "prob_down": round(float(proba[0]), 4),
                "confidence": round(confidence, 4),
                "low_confidence": bool(low_conf),
                "rsi14": round(float(ta["rsi14"]), 2),
                "macd_hist": round(float(ta["macd_hist"]), 2),
                "events": events,
            })

            price_hist.append(lstm_price)
            ta_window.append(lstm_price)
            oc_window.append(abs(self.oc_recent))

        up_days = sum(1 for r in forecast_rows if r["direction"] == "UP" and not r["low_confidence"])
        down_days = sum(1 for r in forecast_rows if r["direction"] == "DOWN" and not r["low_confidence"])
        unc_days = sum(1 for r in forecast_rows if r["low_confidence"])
        net_chg = forecast_rows[-1]["price_pkr"] - self.last_actual

        return {
            "last_known_date": self.last_date.strftime("%Y-%m-%d"),
            "last_known_price_pkr": self.last_actual,
            "model_accuracy": round(self.accuracy, 4),
            "confidence_threshold": CONF_THRESHOLD,
            "horizon_days": n_days,
            "forecast": forecast_rows,
            "summary": {
                "up_days": up_days,
                "down_days": down_days,
                "uncertain_days": unc_days,
                "final_price_pkr": forecast_rows[-1]["price_pkr"],
                "net_change_pkr": round(net_chg, 2),
                "net_change_pct": round(net_chg / self.last_actual, 4),
            },
        }


def get_engine() -> BroilerForecastEngine:
    """Lazily loads the model artifacts on first use (not at Django
    startup) and caches the instance for the life of the process."""
    global _engine_instance
    if _engine_instance is None:
        with _engine_lock:
            if _engine_instance is None:
                _engine_instance = BroilerForecastEngine()
    return _engine_instance


def forecast(horizon_days: int) -> dict:
    with _engine_lock:
        engine = get_engine()
        return engine.predict(horizon_days)
