# REFERENCE.md 
-— Financial Risk Intelligence Domain Knowledge

---

# 1. Financial Feature Definitions

## 1.1 Revenue Growth

**Formula:**
Revenue Growth = (Current Revenue - Previous Revenue) / Previous Revenue

**Business Meaning:**
Measures company expansion. Sustained negative growth signals declining demand or competitive pressure.

---

## 1.2 Profit Margin

**Formula:**
Profit Margin = Net Income / Revenue

**Business Meaning:**
Indicates operational efficiency. Low or negative margins suggest cost pressure or weak pricing power.

---

## 1.3 Debt-to-Equity Ratio

**Formula:**
Debt-to-Equity = Total Debt / Shareholder Equity

**Business Meaning:**
Measures leverage. High values indicate financial risk due to debt burden.

---

## 1.4 Asset Coverage Ratio

**Formula:**
Asset Coverage = Assets / Debt

**Business Meaning:**
Indicates ability to cover liabilities with assets. Low values suggest solvency risk.

---

## 1.5 Operating Cash Flow Ratio

**Formula:**
Operating Cash Flow Ratio = Operating Cash Flow / Revenue

**Business Meaning:**
Reflects real cash generation. Negative values indicate potential liquidity issues.

---

## 1.6 Revenue Volatility

**Formula:**
Standard deviation of revenue growth over recent periods

**Business Meaning:**
High volatility indicates unstable business performance.

---

## 1.7 Revenue Trend

**Formula:**
Rolling average of recent revenue growth

**Business Meaning:**
Captures direction of business momentum (growth vs decline).

---


### 2. Feature Engineering
Derives key financial indicators:

- Revenue Growth  
- Profit Margin  
- Debt-to-Equity  
- Cash Flow Ratio  
- Liability Ratio  
- Revenue Volatility & Trend  

---

### 3. M-Score (Fraud Detection Signals)
Implements Beneish M-Score proxy variables:

- DSRI (Receivables Index)  
- GMI (Gross Margin Index)  
- SGI (Sales Growth Index)  
- TATA (Accruals to Assets)  

These features enhance **fraud and earnings manipulation detection**.

---

### 4. Anomaly Detection (ML Model)
- Algorithm: Isolation Forest  
- Detects unusual financial behavior  
- Trained on full dataset for better context  
- Outputs:
  - Anomaly Flag  
  - Anomaly Score  

---

### 5. Rule-Based Risk Scoring
Deterministic scoring based on:

- Profitability  
- Growth trends  
- Leverage  
- Liquidity  
- Solvency  
- Volatility  
- Anomaly signals  

Outputs:
- Risk Score (0–100)  
- Risk Drivers (explainability)

---

### 6. Model Validation Framework
Combines outputs from ML and rule-based models:

- Agreement check  
- Stability score  
- Anomaly strength  
- Confidence score  

Final decision labels:
- Confirmed Risk  
- Financial Risk  
- Hidden Risk  
- Stable  

---

# 6. Recommendation Templates

## Low Risk

* Maintain current strategy
* Monitor trends periodically

---

## Medium Risk

* Improve margins
* Reduce leverage
* Monitor financial signals closely

---

## High Risk

* Investigate financial distress
* Reduce debt exposure
* Improve liquidity
* Consider restructuring

---

# 7. Industry Benchmarks (General)

| Metric          | Healthy Range |
| --------------- | ------------- |
| Profit Margin   | >10%          |
| Revenue Growth  | >5%           |
| Debt-to-Equity  | <1            |
| Cash Flow Ratio | >10%          |

---

# 8. Assumptions & Limitations

* Based on structured financial data only
* Does not include market sentiment or macro factors
* Risk score is indicative, not predictive
* Industry-specific variations are not fully captured

---
