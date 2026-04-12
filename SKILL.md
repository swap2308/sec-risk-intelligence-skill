---
name: SEC Financial Risk Intelligence Agent

description: An LLM-compatible analytical skill that evaluates company financial health using structured SEC-derived data, combining deterministic modeling, machine learning, and LLM-powered narrative generation to produce explainable financial risk reports.
---

# 🧠 SKILL: SEC Financial Risk Intelligence Agent

## Skill Overview

The **SEC Financial Risk Intelligence Agent** is an end-to-end analytical skill that evaluates company financial health using structured SEC-derived data.

It combines:

* Deterministic financial modeling
* Machine learning (anomaly detection)
* Rule-based scoring
* Model validation
* **LLM-powered narrative generation**

to produce a **fully explainable, executive-ready financial risk report**.

---

## Skill Objective

Given financial data, the agent:

* Assesses financial risk (0–100 score)
* Detects anomalies in financial behavior
* Evaluates financial stability and trends
* Identifies earnings manipulation risk (M-Score)
* Generates **human-readable insights using LLM**
* Produces a **production-grade HTML dashboard report**

---

## Inputs

### Required Dataset

Structured financial table with:

* cik
* name
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

---

## Outputs

### 1. Structured Outputs

* `validation.json` → Data quality report
* `model_output.json` → Risk + anomaly outputs

### 2. Final Output

* `report.html` → Executive dashboard report with:

  * Risk scorecards
  * Threshold flag
  * Charts
  * Validation metrics
  * M-Score analysis
  * **LLM-generated narrative insights**

---

## Skill Pipeline

### Stage 1 — Data Validation

Validates:

* Schema correctness
* Missing values
* Duplicate rows
* Data types

---

### Stage 2 — Feature Engineering

#### Financial Features

* Revenue growth
* Profit margin
* Debt-to-equity
* Cash flow ratio
* Liability ratio
* Revenue trend & volatility

#### M-Score Features (Fraud Detection)

* DSRI
* GMI
* SGI
* TATA

---

### Stage 3 — Risk Modelling

#### Model 1: Rule-Based Scoring

Evaluates:

* Profitability
* Growth
* Leverage
* Liquidity
* Solvency
* Earnings manipulation (M-score contribution)

Outputs:

* Risk score (0–100)
* Risk level (Low / Medium / High)

---

#### Model 2: Anomaly Detection

* Isolation Forest
* Detects unusual financial patterns

Outputs:

* Anomaly flag
* Anomaly strength

---

### Stage 4 — Model Validation

Combines model outputs using:

* Model agreement
* Stability score
* Anomaly strength
* Confidence score

Outputs:

* Final decision label
* Confidence level

---

### Stage 5 — Insight Generation (Deterministic)

Produces structured insights:

* Risk interpretation
* Key drivers
* Recommendations
* M-Score explanation

---

### Stage 6 — LLM Narrative Generation (NEW)

Transforms structured insights into executive language:

Generates:

* Executive summary
* Key drivers (business-readable)
* Red flags
* Risk outlook
* Actionable recommendations

➡️ Enables **decision-ready reporting**

---

### Stage 7 — Report Generation (Enhanced UI)

Creates a **production-grade HTML dashboard**:

Includes:

* Executive summary with scorecards
* Risk threshold indicator (Above / Below)
* Confidence & validation metrics
* Embedded financial charts
* M-Score section (fraud risk)
* LLM-generated narratives
* Business insights & recommendations

---

## Skill Behavior

### Deterministic + AI Hybrid

| Component           | Type             |
| ------------------- | ---------------- |
| Feature Engineering | Deterministic    |
| Risk Scoring        | Rule-based       |
| Anomaly Detection   | Machine Learning |
| Validation          | Deterministic    |
| Narrative           | LLM-powered      |

---

## Key Capabilities

* Explainable financial risk scoring
* Fraud detection via M-Score
* Multi-model validation
* LLM-driven executive insights
* Production-grade reporting UI
* Modular and extensible design

---

## Example Skill Execution

### Input

```json
{
  "company": "MATSON, INC.",
  "periods": 7
}
```

### Output (Summary)

* Risk Score: 15
* Risk Level: Low
* Confidence: 88%
* Decision: Stable
* M-Score: Medium Risk

### LLM Insight (Example)

> The company shows stable financial performance with low risk exposure.
> No significant anomaly signals are detected.
> However, moderate M-Score suggests monitoring earnings quality.

---

## Agentic Compatibility

This skill is designed for **LLM orchestration frameworks**:

* Can be invoked as a tool in multi-agent workflows
* Supports structured input/output
* Produces both machine-readable and human-readable outputs
* Enables reasoning + reporting separation

---

## Limitations

* Dependent on structured financial data quality
* Does not include macroeconomic or market signals
* Industry-specific normalization not applied
* LLM outputs may vary slightly based on prompt

---

## Future Enhancements

* SEC filing text analysis (MD&A, footnotes)
* Market + sentiment integration
* Peer comparison engine
* Forecasting models
* SHAP-based explainability
* Interactive dashboards (Streamlit)

---

## Summary

The **SEC Financial Risk Intelligence Skill** is a **production-ready, explainable AI system** that combines:

* Financial analytics
* Machine learning
* Validation logic
* LLM-powered narratives

to deliver **actionable, executive-grade financial risk intelligence**.

---
