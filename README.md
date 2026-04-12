
---

# 📊 SEC Financial Risk Intelligence

## Overview

The **SEC Financial Risk Intelligence Agent** is a **production-grade, end-to-end financial analytics system** that evaluates company health using structured financial data.
"The goal was to build a skill that a credit analyst, risk officer, or portfolio manager could use without needing a data-science background — making explainability as important as accuracy."

It combines:

* Deterministic analytics (feature engineering + scoring)
* Machine learning (anomaly detection)
* Validation logic (multi-model agreement)
* **LLM-powered narrative generation**
* **Executive-grade HTML dashboard reporting**

The system is designed as an **LLM-compatible analytical skill** capable of generating **explainable, audit-ready financial risk reports**.

---
## How skill can be used

Skill can be added to claude.ai ,in setting-> cababilities-> add skills
### NOTE:
The current solution is integrated with GROQ using llama-3.3-70b-versatile Model ,hence if we upload the same skill on claude.ai it will execute the skill.md using anthropic over riding Groq

---
* **name: sec-risk-intelligence-skill**
description: When to trigger this skill and what it does.

## Objective

To analyze company financial data and:

* Detect financial risk
* Identify anomalies
* Evaluate financial stability and trends
* Detect earnings manipulation (M-Score)
* Generate **human-readable executive insights (LLM-powered)**
* Produce a **production-grade business report**

---

## Project Structure

```plaintext
SEC-RISK-INTELLIGENCE-SKILL/
│
├── data/
│ ├── Data_Dictionary.xlsx
│ ├── financial_table.csv
│ ├── financial_bad_data.csv
│ ├── financial_high_risk.csv
│ ├── financial_manipulated_data.csv
│
├── documents/
│ ├── Design_Walkthrough.pdf
│ ├── Evaluation_report.docx
│
├── output/
│ ├── run1_normal/
│ ├── run2_stressed/
│ ├── run3_bad_data/
│ ├── run4_manipulated_data/
│ ├── consolidated_analysis.json
│ ├── consolidated_report.html
│ ├── revenue.png
│ ├── net_income.png
│ ├── run_summary.json
│ ├── Sample_output.json
│ ├── validation.json
│
├── scripts/
│ ├── analytics_model.py
│ ├── data_validation.py
│ ├── insight_generator.py
│ ├── llm_insights.py
│ ├── report_generator.py
│ ├── main.py
│ ├── output/ (generated outputs)
│
├── prompts/
│
├── REFERENCE.md
├── SKILL.md
└── README.md
```

---

## Dataset

The dataset contains structured financial data derived from SEC filings.The default financial_table.csv was curated using data from SEC directly and only the require attributes were extracted for the solution

### Required Columns

* cik
* ddate
* revenue
* net_income
* assets
* liabilities
* debt
* equity
* cash_flow
* receivables
* cogs
* name

---

## Analytics Pipeline

The system follows a **7-stage hybrid pipeline (deterministic + AI)**:

---

### 1. Data Validation & Profiling

Validates:

* Schema consistency
* Missing values
* Duplicates
* Data types

📄 Output: `validation.json`

---

### 2. Feature Engineering

#### Core Financial Features

* Revenue growth
* Profit margin
* Debt-to-equity
* Cash flow ratio
* Liability ratio
* Revenue volatility
* Revenue trend

#### M-Score (Fraud Detection Layer)

* DSRI – Days Sales in Receivables Index
* GMI – Gross Margin Index
* SGI – Sales Growth Index
* TATA – Total Accruals to Total Assets

➡️ Used to detect **earnings manipulation risk**

---

### 3. Modelling

#### Model 1: Rule-Based Risk Scoring

Evaluates:

* Profitability
* Growth
* Leverage
* Liquidity
* Solvency
* M-Score contribution

#### Model 2: Anomaly Detection

* Isolation Forest
* Detects abnormal financial behavior

---

### 4. Model Validation

Cross-validates outputs using:

* Model agreement
* Stability score
* Anomaly strength
* Confidence score

---

### 5. Insight Generation

Produces structured insights:

* Risk interpretation
* Key drivers
* Recommendations
* M-Score explanation

---

### 6. LLM Narrative Generation (NEW)

Uses GPT-based model to generate:

* Executive summary
* Key risk drivers (human-readable)
* Red flags
* Forward-looking risk outlook
* Business recommendations

➡️ Converts structured outputs into **decision-ready insights**

---

### 7. Report Generation (Enhanced)

Generates a **production-grade HTML dashboard** including:

* Executive summary with scorecards
* Risk threshold flag (Above/Below)
* Model confidence indicators
* Embedded charts (base64)
* Validation metrics
* M-Score (earnings risk)
* LLM-generated narrative sections
* Business interpretation & recommendations

---

## Outputs

| File                | Description                        |
| ------------------- | ---------------------------------- |
| `validation.json`   | Data quality report                |
| `model_output.json` | Risk + anomaly results             |
| `report.html`       | Executive dashboard report (final) |

---

## How to Run

### Run Full Pipeline

```bash
python scripts/main.py \
  --input-data data/financial_table.csv \
  --output-report outputs/report.html
```

## Sample Output

### Risk Summary

* Risk Score: 15
* Risk Level: Low
* Confidence: 88%
* Decision: Stable

### LLM Executive Insight (Example)

> The company demonstrates stable financial performance with low risk exposure.
> Revenue trends remain consistent, leverage is controlled, and no strong anomaly signals are detected.
> However, moderate M-Score signals suggest monitoring earnings quality.

---

## Key Features

* Deterministic + AI hybrid pipeline
* Multi-model validation
* M-Score fraud detection
* **LLM-powered business narratives**
* Production-grade HTML dashboard
* Explainable risk scoring
* Modular architecture (plug-and-play)
* Fully auditable outputs

---

## Limitations

* Based only on financial statement data
* No macroeconomic or market sentiment integration
* Industry-specific adjustments not included
* LLM output depends on prompt quality
* Risk score is indicative, not predictive

---

## Future Enhancements

* NLP on SEC filings (MD&A, footnotes)
* Market + sentiment data integration
* Peer benchmarking
* Forecasting & scenario simulation
* SHAP-based explainability
* Interactive dashboard (Streamlit / Plotly)
* Multi-company comparison reports

---

## Conclusion

This project delivers a **production-ready financial intelligence system** that combines:

* Financial analytics
* Machine learning
* Explainable AI
* LLM-driven storytelling

to generate **actionable, executive-level financial risk insights**.

---
