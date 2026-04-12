"""
analytics_model.py

Performs:
1. Feature engineering
2. Anomaly detection (Isolation Forest)
3. Risk scoring (rule-based v2)
4. Model validation & comparison

Input:
    CSV file with financial data

Output:
    outputs/model_output.json
"""
import pandas as pd
import numpy as np
import json
import argparse
import os
import sys

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# ─────────────────────────────────────────────────────────────
# Feature Engineering
# ─────────────────────────────────────────────────────────────
def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived financial features per company, preserving all rows."""
    df = df.copy()
    df = df.sort_values(['cik', 'ddate'])

    grp = df.groupby('cik')

    df['prev_revenue']      = grp['revenue'].shift(1)
    df['revenue_growth']    = (df['revenue'] - df['prev_revenue']) / (df['prev_revenue'].abs() + 1e-6)
    df['profit_margin']     = df['net_income'] / (df['revenue'] + 1e-6)
    df['debt_to_equity']    = df['debt']       / (df['equity']   + 1e-6)
    df['cash_flow_ratio']   = df['cash_flow']  / (df['revenue']  + 1e-6)
    df['liability_ratio']   = df['liabilities']/ (df['assets']   + 1e-6)

    pct_chg = grp['revenue'].pct_change()
    df['revenue_volatility'] = (
        pct_chg.rolling(3, min_periods=1).std().reset_index(level=0, drop=True)
    )
    df['revenue_trend'] = (
        pct_chg.rolling(3, min_periods=1).mean().reset_index(level=0, drop=True)
    )

    return df


# ─────────────────────────────────────────────────────────────
# M-Score Features  
# ─────────────────────────────────────────────────────────────
def prepare_m_score_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Beneish M-Score proxy indices.


            no rows are silently lost before anomaly detection.
    """
    df = df.copy()
    df = df.sort_values(['cik', 'ddate'])
    grp = df.groupby('cik')

    # DSRI – Days Sales in Receivables Index
    recv_ratio      = df['receivables'] / (df['revenue'] + 1e-6)
    prev_recv_ratio = grp['receivables'].shift(1) / (grp['revenue'].shift(1) + 1e-6)
    df['dsri'] = recv_ratio / (prev_recv_ratio + 1e-6)

    # GMI – Gross Margin Index
    prev_rev  = grp['revenue'].shift(1)
    prev_cogs = grp['cogs'].shift(1)
    df['prev_gm'] = (prev_rev - prev_cogs) / (prev_rev + 1e-6)
    df['curr_gm'] = (df['revenue'] - df['cogs']) / (df['revenue'] + 1e-6)
    df['gmi']     = df['prev_gm'] / (df['curr_gm'] + 1e-6)

    # SGI – Sales Growth Index  
    df['sgi'] = df['revenue'] / (grp['revenue'].shift(1) + 1e-6)

    # TATA – Total Accruals to Total Assets
    df['tata'] = (df['net_income'] - df['cash_flow']) / (df['assets'] + 1e-6)

    
    for col in ['dsri', 'gmi', 'sgi', 'tata']:
        median_val = df[col].replace([np.inf, -np.inf], np.nan).median()
        df[col] = df[col].replace([np.inf, -np.inf], np.nan).fillna(median_val)

    return df          #  no dropna(); all rows preserved


# ─────────────────────────────────────────────────────────────
# Anomaly Detection
# ─────────────────────────────────────────────────────────────
def detect_anomalies(df_full: pd.DataFrame, df_target: pd.DataFrame):
    """
     Train Isolation Forest on the full dataset for a rich
    reference distribution; score only the target company's rows.

    Returns df_target with anomaly_flag and anomaly_score columns added.
    """
    features = ['dsri', 'gmi', 'sgi', 'tata', 'debt_to_equity', 'profit_margin']

    def clean(frame):
        X = frame[features].replace([np.inf, -np.inf], np.nan)
        return X.fillna(X.median())

    X_full   = clean(df_full)
    X_target = clean(df_target)

    scaler  = StandardScaler()
    X_full_scaled   = scaler.fit_transform(X_full)
    X_target_scaled = scaler.transform(X_target)

    model = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
    model.fit(X_full_scaled)

    df_target = df_target.copy()
    df_target['anomaly_flag']  = model.predict(X_target_scaled)
    df_target['anomaly_score'] = model.decision_function(X_target_scaled)

    return df_target


# ─────────────────────────────────────────────────────────────
# Risk Model  
# ─────────────────────────────────────────────────────────────
def compute_risk_score(df: pd.DataFrame):
    """
    Rule-based risk scoring on the latest period of the target company.

    Solvency check (liabilities > assets) is now guarded with
            pd.notna() so a NaN in either column does not raise TypeError.
    """
    df     = df.sort_values('ddate')
    latest = df.iloc[-1]

    risk    = 0
    drivers = []

    # Profitability
    pm = latest['profit_margin']
    if pd.notna(pm):
        if pm < 0:
            risk += 30; drivers.append("Negative profitability")
        elif pm < 0.05:
            risk += 15; drivers.append("Low profit margin (<5%)")

    # Revenue growth
    growth = latest['revenue_growth']
    if pd.notna(growth):
        if growth < -0.10:
            risk += 30; drivers.append("Sharp revenue decline (>10%)")
        elif growth < 0:
            risk += 20; drivers.append("Declining revenue")

    # Leverage
    dte = latest['debt_to_equity']
    if pd.notna(dte):
        if dte > 3:
            risk += 30; drivers.append("Very high leverage (D/E > 3)")
        elif dte > 2:
            risk += 20; drivers.append("High leverage (D/E > 2)")

    # Cash flow
    cf = latest['cash_flow']
    if pd.notna(cf) and cf < 0:
        risk += 25; drivers.append("Negative operating cash flow")

    # Solvency  null-safe comparison
    liab  = latest.get('liabilities')
    assets = latest.get('assets')
    if pd.notna(liab) and pd.notna(assets) and liab > assets:
        risk += 25; drivers.append("Liabilities exceed assets")

    # Volatility
    vol = latest.get('revenue_volatility', np.nan)
    if pd.notna(vol) and vol > 0.3:
        risk += 10; drivers.append("High revenue volatility")

    # Anomaly signal
    if latest.get('anomaly_flag') == -1:
        risk += 20; drivers.append("Statistical anomaly detected")
        
    # M-score proxy (simple weighted signal)
    m_score_signal = (
    0.9 * latest['dsri'] +
    0.5 * latest['gmi'] +
    0.7 * latest['sgi'] +
    1.2 * latest['tata']
   )

    if pd.notna(m_score_signal):
        if m_score_signal > 2.5:
            risk += 25; drivers.append("High earnings manipulation risk (M-score)")
        elif m_score_signal > 1.5:
            risk += 15; drivers.append("Moderate earnings manipulation risk")

    if not drivers:
        drivers.append("No major risk factors identified")

    return min(risk, 100), drivers


# ─────────────────────────────────────────────────────────────
# Model Validation  
# ─────────────────────────────────────────────────────────────
def validate_models(df: pd.DataFrame, risk_score: int) -> dict:
    """
    Compare rule-based and anomaly-detection bands; compute confidence.

     volatility NaN is handled before max(0, 1 - v) so stability
            never silently becomes NaN.
    """
    latest        = df.sort_values('ddate').iloc[-1]
    anomaly_flag  = 1 if latest['anomaly_flag'] == -1 else 0
    anomaly_score = float(latest['anomaly_score'])

    rule_band    = "high" if risk_score >= 70 else ("medium" if risk_score >= 40 else "low")
    anomaly_band = "high" if anomaly_flag else "low"
    
    # Compute m_score_signal locally
    m_score_signal = (
        0.9 * latest['dsri'] +
        0.5 * latest['gmi'] +
        0.7 * latest['sgi'] +
        1.2 * latest['tata']
    )
    
    m_score_band = "high" if pd.notna(m_score_signal) and m_score_signal > 2.5 else ("medium" if pd.notna(m_score_signal) and m_score_signal > 1.5 else "low")
    agreement    = rule_band == anomaly_band

    #  guard against NaN volatility
    raw_vol  = df['revenue'].pct_change().std()
    vol      = raw_vol if pd.notna(raw_vol) else 0.0
    stability = float(max(0.0, 1.0 - vol))

    strength   = float(max(0.0, -anomaly_score))
    confidence = round((
        0.3 * min(1.0, len(df) / 5) +
        0.3 * (1.0 if agreement else 0.5) +
        0.2 * stability +
        0.2 * (1.0 - min(strength, 1.0))
    ) * 100, 2)

    # Narrative decision label
    if rule_band == "high" and anomaly_band == "high":
        decision = "Confirmed Risk"
    elif rule_band == "high":
        decision = "Financial Risk"
    elif anomaly_band == "high":
        decision = "Hidden Risk"
    else:
        decision = "Stable"

    return {
        "agreement":       agreement,      
        "stability_score": stability,     
        "anomaly_strength": strength,
        "confidence_score": confidence,
        "rule_band":        rule_band,
        "anomaly_band":     anomaly_band,
        "decision":         decision,
        "m_score_band":     m_score_band,
        "m_score_signal":   float(round(m_score_signal, 2)) if pd.notna(m_score_signal) else None
    }


# ─────────────────────────────────────────────────────────────
# Main 
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="SEC Financial Risk Model")
    parser.add_argument("--input-data", required=True,  help="Path to financial CSV")
    parser.add_argument("--cik",        required=True,  type=int, help="Target company CIK")
    parser.add_argument("--output",     default="outputs/model_output.json")
    args = parser.parse_args()

    try:
        df_raw = pd.read_csv(args.input_data)
        df_raw['ddate'] = pd.to_datetime(df_raw['ddate'])

        # filter BEFORE feature engineering so the risk model scores
        #         only the target company, not whatever row happens to be last.
        df_target_raw = df_raw[df_raw['cik'] == args.cik].copy()
        if df_target_raw.empty:
            raise ValueError(f"No rows found for CIK {args.cik}")

        # Feature engineering on full dataset (for proper anomaly context)
        df_full   = compute_features(df_raw)
        df_full   = prepare_m_score_features(df_full)

        # Isolate target AFTER feature engineering
        df_target = df_full[df_full['cik'] == args.cik].copy()

        # Anomaly detection: train on full, score on target
        df_target = detect_anomalies(df_full, df_target)

        # Risk scoring and validation on target only
        risk_score, drivers = compute_risk_score(df_target)
        validation          = validate_models(df_target, risk_score)
        

        risk_level = "High" if risk_score >= 70 else ("Medium" if risk_score >= 40 else "Low")
        latest     = df_target.sort_values('ddate').iloc[-1]

        output = {
            "company":    str(latest.get("name", "Unknown")),
            "cik":        int(latest["cik"]),
            "risk_score": int(risk_score),
            "risk_level": risk_level,
            "drivers":    drivers,
            "anomaly": {
                "is_anomaly":    int(latest['anomaly_flag'] == -1),
                "anomaly_score": float(latest['anomaly_score']),
            },
            "m_score": {
            "m_score": float(validation['m_score_band']),
            "m_score_risk": "High" if validation['m_score_band'] > 2.5 else ("Medium" if validation['m_score_band'] > 1.5 else "Low"),
            "validation": validation,
        }
        }

        os.makedirs(os.path.dirname(args.output) or "outputs", exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(output, f, indent=4)

        print(json.dumps(output, indent=2))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
