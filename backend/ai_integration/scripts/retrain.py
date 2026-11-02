"""
Retrains the broiler price forecast model (LSTM momentum model +
XGBoost direction classifier) from an updated source CSV, and writes
fresh artifacts into `ai_integration/ml_artifacts/`.

This is a straight port of the training notebook's cells (config,
feature engineering, LSTM training, label creation, XGBoost training,
save) — same hyperparameters, same architecture, same feature set. Run
it whenever fresh source data (extending `agbro_broiler_prices_v8_with
_feed_final.csv`, or whatever it's renamed to) is available.

Usage (from the poultry_backend/ directory, with the venv active):

    python manage.py shell -c "from ai_integration.scripts.retrain import main; main('/path/to/updated_source.csv')"

or directly:

    DJANGO_SETTINGS_MODULE=poultry_backend.settings python -m ai_integration.scripts.retrain /path/to/updated_source.csv

This overwrites the live artifacts, so the *next* price-forecast request
picks up the freshly trained model automatically (it's loaded lazily and
cached in-process — restart the Django process to force a reload if one
is already running).
"""

import json
import os
import sys

import numpy as np
import pandas as pd

TARGET = "lhr_farm"
LOOKBACK = 28
HORIZON = 1
BAND = 0.005
TEST_SIZE = 60
VAL_SIZE = 60


def main(source_csv_path: str, artifacts_dir: str | None = None):
    from ..inference import broiler_features as feat

    if artifacts_dir is None:
        artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_artifacts")

    print(f"Loading source data: {source_csv_path}")
    df_raw = pd.read_csv(source_csv_path)
    print(f"  {df_raw.shape[0]} rows x {df_raw.shape[1]} columns, "
          f"{df_raw['date'].iloc[0]} to {df_raw['date'].iloc[-1]}")

    print("Running feature pipeline...")
    df = feat.prepare_dataset(df_raw)
    print(f"  Prepared: {len(df)} rows. Price range: {df[TARGET].min():.0f}-{df[TARGET].max():.0f} PKR")

    # ---- Train LSTM (momentum model) --------------------------------
    from sklearn.preprocessing import MinMaxScaler
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.models import Sequential
    import tensorflow as tf

    tf.random.set_seed(42)
    np.random.seed(42)

    n_total = len(df)
    te_start = n_total - TEST_SIZE
    va_start = te_start - VAL_SIZE

    price_scaler = MinMaxScaler()
    price_scaler.fit(df.iloc[:va_start][[TARGET]])
    full_scaled = price_scaler.transform(df[[TARGET]]).flatten()

    def make_sequences(arr, lb):
        X, y = [], []
        for i in range(lb, len(arr)):
            X.append(arr[i - lb:i])
            y.append(arr[i])
        return np.array(X), np.array(y)

    X_all, y_all = make_sequences(full_scaled, LOOKBACK)
    tr_end = va_start - LOOKBACK
    va_end = te_start - LOOKBACK

    X_tr = X_all[:tr_end].reshape(-1, LOOKBACK, 1)
    y_tr = y_all[:tr_end]
    X_va = X_all[tr_end:va_end].reshape(-1, LOOKBACK, 1)
    y_va = y_all[tr_end:va_end]

    print(f"Training LSTM (lookback={LOOKBACK}d, {len(X_tr)} train / {len(X_va)} val sequences)...")
    lstm_model = Sequential([
        LSTM(64, input_shape=(LOOKBACK, 1), return_sequences=True),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1),
    ])
    lstm_model.compile(optimizer="adam", loss="mse")
    es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)
    history = lstm_model.fit(
        X_tr, y_tr, validation_data=(X_va, y_va),
        epochs=100, batch_size=32, callbacks=[es], verbose=0,
    )
    print(f"  Trained in {len(history.history['loss'])} epochs, "
          f"final val_loss={min(history.history['val_loss']):.5f}")

    # ---- LSTM-implied change feature + direction labels --------------
    all_X = np.array([full_scaled[i - LOOKBACK:i] for i in range(LOOKBACK, n_total)]).reshape(-1, LOOKBACK, 1)
    pred_sc = lstm_model.predict(all_X, verbose=0).flatten()
    pred_p = price_scaler.inverse_transform(pred_sc.reshape(-1, 1)).flatten()

    lstm_chg = np.full(n_total, 0.0)
    lstm_chg[LOOKBACK:] = (
        (pred_p - df[TARGET].values[LOOKBACK - 1:n_total - 1]) / df[TARGET].values[LOOKBACK - 1:n_total - 1]
    )
    df["lstm_implied_chg"] = lstm_chg

    future_price = df[TARGET].shift(-HORIZON)
    pct_change = (future_price - df[TARGET]) / df[TARGET]
    df["label"] = np.where(pct_change < -BAND, 0, np.where(pct_change > BAND, 1, np.nan))

    required = ["label", "lag_7", "roc_10", "usdpkr_roll7", "feed_roll3m", "rsi14", "vol21", "macd_signal"]
    df_model = df.dropna(subset=required).reset_index(drop=True)
    df_model["label"] = df_model["label"].astype(int)
    print(f"  Labels: DOWN={int((df_model['label']==0).sum())}  UP={int((df_model['label']==1).sum())}"
          f"  ({len(df_model)} usable rows)")

    # ---- Train XGBoost direction classifier --------------------------
    from sklearn.metrics import accuracy_score
    from xgboost import XGBClassifier

    n2 = len(df_model)
    te_s = n2 - TEST_SIZE
    va_s = te_s - VAL_SIZE
    tr_df = df_model.iloc[:va_s]
    va_df = df_model.iloc[va_s:te_s]
    te_df = df_model.iloc[te_s:].reset_index(drop=True)

    print("Training XGBoost direction classifier...")
    clf = XGBClassifier(
        n_estimators=400, max_depth=4, learning_rate=0.04,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        objective="binary:logistic", eval_metric="logloss",
        early_stopping_rounds=25,
    )
    clf.fit(
        tr_df[feat.ALL_FEATS], tr_df["label"],
        eval_set=[(va_df[feat.ALL_FEATS], va_df["label"])],
        verbose=False,
    )

    y_test = te_df["label"].values
    y_pred = clf.predict(te_df[feat.ALL_FEATS])
    accuracy = float(accuracy_score(y_test, y_pred))
    print(f"  Held-out test accuracy ({TEST_SIZE} days): {accuracy:.1%}")

    # ---- Save artifacts (native, pickle-free formats) -----------------
    os.makedirs(artifacts_dir, exist_ok=True)
    import hashlib

    def _write(relpath: str, write_fn):
        path = os.path.join(artifacts_dir, relpath)
        write_fn(path)
        return path

    lstm_path = _write("lstm_model_28.keras", lambda p: lstm_model.save(p))
    clf_path = _write("xgboost_clf.json", lambda p: clf.save_model(p))
    scaler_path = _write(
        "price_scaler.json",
        lambda p: json.dump(
            {"min_": price_scaler.min_.tolist(), "scale_": price_scaler.scale_.tolist()}, open(p, "w")
        ),
    )
    metrics_path = _write("metrics.json", lambda p: json.dump({"accuracy": accuracy}, open(p, "w")))
    history_path = _write(
        "prepared_history.csv",
        # Only the raw + engineered columns the inference engine actually
        # reads — matches the shape of the previous prepared_history.csv.
        lambda p: df.drop(columns=["label"], errors="ignore").to_csv(p, index=False),
    )

    artifact_paths = [lstm_path, clf_path, scaler_path, metrics_path, history_path]

    def _md5_of(path, chunk_size=1024 * 1024):
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                h.update(chunk)
        return h.hexdigest()

    manifest = {
        os.path.basename(p): {"size": os.path.getsize(p), "md5": _md5_of(p)} for p in artifact_paths
    }
    manifest_path = os.path.join(artifacts_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nSaved artifacts to {artifacts_dir}:")
    for p in artifact_paths + [manifest_path]:
        print(f"  {os.path.basename(p):28s} {os.path.getsize(p):>10,} bytes")
    print(f"\nLast known date: {df['_date'].iloc[-1].date()}  price: {df[TARGET].iloc[-1]:.0f} PKR")
    print(f"Model accuracy: {accuracy:.1%}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ai_integration.scripts.retrain <path-to-source-csv>")
        sys.exit(1)
    main(sys.argv[1])
