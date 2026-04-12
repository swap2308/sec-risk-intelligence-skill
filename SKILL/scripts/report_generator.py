"""
report_generator.py  

Performs:
1. Chart generation (revenue, net income trends)
2. HTML report creation with embedded charts and validation metrics
"""

import re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import json
import os

# -----------------------------
# LLM JSON PARSER (FIX)
# -----------------------------

def extract_json_object(text):
    if not text:
        return None

    cleaned = text.strip()
    start = cleaned.find("{")
    if start == -1:
        return None

    stack = []
    for idx in range(start, len(cleaned)):
        ch = cleaned[idx]
        if ch == "{":
            stack.append(ch)
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack:
                    return cleaned[start:idx + 1]
    return None


def safe_parse_llm_output(text):
    cleaned = (text or "").strip()

    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = re.sub(r"^json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^#+\s*JSON Response:?", "", cleaned, flags=re.IGNORECASE)

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    candidate = extract_json_object(cleaned) or extract_json_object(text)
    if candidate:
        try:
            return json.loads(candidate)
        except Exception:
            pass

    fallback_text = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    fallback_text = re.sub(r"[`*\"]", "", fallback_text)
    fallback_text = re.sub(r"JSON Response:.*", "", fallback_text, flags=re.IGNORECASE | re.DOTALL).strip()

    return {
        "executive_summary": fallback_text or "No executive summary available.",
        "key_drivers": [],
        "risk_outlook": "",
        "red_flags": [],
        "recommendations": []
    }


# -----------------------------
# FORMAT LLM OUTPUT
# -----------------------------
def format_llm_section(llm_json):

    exec_summary = llm_json.get("executive_summary", "No executive summary available.")
    risk_outlook = llm_json.get("risk_outlook", "No outlook available.")
    key_drivers = llm_json.get("key_drivers") or llm_json.get("risk_analysis") or []
    red_flags = llm_json.get("red_flags", [])
    recommendations = llm_json.get("recommendations", [])

    drivers_html = "".join(f"<li>{d}</li>" for d in key_drivers)
    flags_html = "".join(f"<li>{f}</li>" for f in red_flags)
    recs_html = "".join(f"<li>{r}</li>" for r in recommendations)

    return f"""
    <div class="llm-section">
        <h3>Executive Summary</h3>
        <p>{exec_summary}</p>

        <h3>Key Drivers</h3>
        <ul>{drivers_html if drivers_html else '<li>No major drivers identified</li>'}</ul>

        <h3>Red Flags</h3>
        <ul>{flags_html if flags_html else '<li>No red flags identified</li>'}</ul>

        <h3>Risk Outlook</h3>
        <p>{risk_outlook}</p>

        <h3>Recommendations</h3>
        <ul>{recs_html if recs_html else '<li>No recommendations provided</li>'}</ul>
    </div>
    """
# ─────────────────────────────────────────────────────────────
# Charts
# ─────────────────────────────────────────────────────────────
def create_charts(df: pd.DataFrame, out_dir: str = "output") -> None:
    os.makedirs(out_dir, exist_ok=True)
    df = df.sort_values('ddate')

    for col, title, fname in [
        ('revenue',    'Revenue Trend',    'revenue.png'),
        ('net_income', 'Net Income Trend', 'net_income.png'),
    ]:
        if col not in df.columns:
            continue
        fig, ax = plt.subplots()
        ax.plot(df['ddate'], df[col], marker='o')
        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_ylabel('USD')
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, fname))
        plt.close(fig)


# ─────────────────────────────────────────────────────────────
# HTML Report
# ─────────────────────────────────────────────────────────────
import base64

def encode_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

import base64
from datetime import datetime
import os

from llm_insights import generate_llm_narrative


def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def generate_report(prompt, run_id, df, insights, validation, output_path=None):

    if output_path is None:
        output_path = f"output/{run_id}/report.html"

    out_dir = os.path.dirname(output_path) or "output"
    create_charts(df, out_dir)
    # Encode charts
    revenue_img = encode_image(os.path.join(out_dir, "revenue.png"))
    income_img  = encode_image(os.path.join(out_dir, "net_income.png"))

    # LLM narrative (NEW)
   # llm_output = generate_llm_narrative(prompt,
        #insights,
      #  validation,
      #  df.tail(1)
    #)
     # -----------------------------
    # LLM PARSE + FORMAT
    # -----------------------------
    llm_raw = generate_llm_narrative(prompt,
        insights,
        validation,
        df.tail(1)
    )
    
    if isinstance(llm_raw, str):
        llm_json = safe_parse_llm_output(llm_raw)
    else:
        llm_json = llm_raw

    llm_output = format_llm_section(llm_json)

    # Extract values
    risk_score = insights.get("risk_score", 0)
    confidence = validation.get("confidence_score", 0)
    decision   = validation.get("decision", "N/A")
    m_score    = insights.get("m_score", {}).get("value", "N/A")
    m_risk     = insights.get("m_score", {}).get("risk_level", "N/A")
    llm_html   = llm_output

    threshold = 70
    flag_class = "below" if risk_score < threshold else "above"
    flag_text  = "WITHIN THRESHOLD" if risk_score < threshold else "ABOVE THRESHOLD"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Financial Risk Intelligence Report</title>

<style>
body {{ font-family:'Segoe UI'; background:#f0f4f8; margin:0; }}

.header {{
    background:linear-gradient(135deg,#1a56db,#1e3a8a);
    color:white;padding:35px;
}}

.container {{ max-width:1200px;margin:auto;padding:20px; }}

.card {{
    background:white;border-radius:12px;
    padding:22px;margin-bottom:20px;
    box-shadow:0 2px 12px rgba(0,0,0,.08);
}}

.score-grid {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:15px;
}}

.sc {{ text-align:center;padding:18px;border:1px solid #eee;border-radius:10px; }}
.val {{ font-size:1.8rem;font-weight:800; }}
.lbl {{ font-size:.75rem;color:#666;margin-top:5px;text-transform:uppercase; }}

.flag {{
    padding:14px;border-radius:8px;margin-bottom:15px;
    font-weight:700;
}}

.flag.below {{ background:#def7ec;color:#065f46; }}
.flag.above {{ background:#fde8e8;color:#c53030; }}

img {{ width:100%; border-radius:8px;margin-top:10px; }}
.llm-section {{
    background:#fafbfe;
    border:1px solid #dbeafe;
    padding:20px;
    border-radius:12px;
}}

.llm-section h3 {{
    margin-top:20px;
    margin-bottom:10px;
    color:#1e3a8a;
}}

.llm-section p {{
    line-height:1.7;
    color:#334155;
    margin:0 0 14px;
}}

.llm-section ul {{
    margin:0 0 16px;
    padding-left:20px;
}}

.llm-section li {{ margin-bottom:10px; color:#475569; }}
ul li {{ margin-bottom:8px; }}

</style>
</head>

<body>

<div class="header">
<h1>📊 Financial Risk Intelligence Report</h1>
<p>Generated: {datetime.now()}</p>
</div>

<div class="container">

<div class="flag {flag_class}">
{flag_text} — Threshold {threshold}
</div>

<!-- EXEC SUMMARY -->
<div class="card">
<h2>Executive Summary</h2>

<div class="score-grid">
  <div class="sc"><div class="val">{risk_score}</div><div class="lbl">Risk Score</div></div>
  <div class="sc"><div class="val">{confidence}%</div><div class="lbl">Confidence</div></div>
  <div class="sc"><div class="val">{decision}</div><div class="lbl">Decision</div></div>
  <div class="sc"><div class="val">{m_score}</div><div class="lbl">M-Score</div></div>
  <div class="sc"><div class="val">{m_risk}</div><div class="lbl">M-Risk</div></div>
</div>

</div>

<!-- CHARTS -->
<div class="card">
<h2>Financial Trends</h2>
<img src="data:image/png;base64,{revenue_img}">
<img src="data:image/png;base64,{income_img}">
</div>

<div class="card">
<h2>LLM Narrative</h2>
{llm_html}
</div>

</div>
</body>
</html>
"""

    os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path
  