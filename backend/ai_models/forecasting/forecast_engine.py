"""Demand forecasting engine using Holt-Winters Exponential Smoothing."""
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sqlalchemy.orm import Session

from models import DemandHistory


def get_demand_dataframe(db: Session, product_id: int) -> pd.DataFrame:
    """Fetch demand history for a product and return as a DataFrame."""
    records = (
        db.query(DemandHistory)
        .filter(DemandHistory.product_id == product_id)
        .order_by(DemandHistory.date)
        .all()
    )
    if not records:
        return pd.DataFrame(columns=["date", "quantity"])

    data = [{"date": r.date, "quantity": r.quantity} for r in records]
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.asfreq("D", fill_value=0)
    return df


def forecast_demand(db: Session, product_id: int, periods: int = 30):
    """
    Train Holt-Winters model on historical demand and forecast future periods.

    Returns dict with:
      - history: list of {date, actual}
      - forecast: list of {date, predicted, lower, upper}
      - summary: {avg_predicted, peak_date, peak_value, total_forecasted}
    """
    df = get_demand_dataframe(db, product_id)

    if len(df) < 14:
        return {"error": "Insufficient data. Need at least 14 days of demand history."}

    # Ensure all values are positive for multiplicative model
    y = df["quantity"].values.astype(float)
    y = np.maximum(y, 0.1)  # avoid zeros for multiplicative seasonality

    try:
        # Fit Holt-Winters with weekly seasonality (period=7)
        model = ExponentialSmoothing(
            y,
            seasonal_periods=7,
            trend="add",
            seasonal="add",
            initialization_method="estimated",
        )
        fitted = model.fit(optimized=True)

        # Forecast
        pred = fitted.forecast(periods)

        # Calculate confidence intervals using residual std
        residuals = fitted.resid
        std = np.std(residuals)
        z = 1.28  # ~80% confidence interval

    except Exception:
        # Fallback to simple moving average if Holt-Winters fails
        window = min(14, len(y))
        avg = np.mean(y[-window:])
        std = np.std(y[-window:])
        pred = np.full(periods, avg)
        z = 1.28

    # Build history
    dates = df.index.tolist()
    history = [
        {
            "date": dates[i].strftime("%Y-%m-%d"),
            "actual": int(df["quantity"].iloc[i]),
        }
        for i in range(len(df))
    ]

    # Build forecast
    last_date = dates[-1]
    forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq="D")
    forecast = [
        {
            "date": forecast_dates[i].strftime("%Y-%m-%d"),
            "predicted": round(float(pred[i]), 1),
            "lower": round(float(max(0, pred[i] - z * std)), 1),
            "upper": round(float(pred[i] + z * std), 1),
        }
        for i in range(periods)
    ]

    # Summary
    avg_pred = round(float(np.mean(pred)), 1)
    total = round(float(np.sum(pred)), 0)
    peak_idx = int(np.argmax(pred))
    summary = {
        "avg_daily_demand": avg_pred,
        "total_forecasted": total,
        "peak_date": forecast_dates[peak_idx].strftime("%Y-%m-%d"),
        "peak_value": round(float(pred[peak_idx]), 1),
    }

    return {
        "product_id": product_id,
        "periods": periods,
        "history": history,
        "forecast": forecast,
        "summary": summary,
    }
