import sys
import subprocess

from typer import prompt

#from SKILL.scripts.insight_generator import enhance_insights_with_llm
from data_validation import run_validation
from analytics_model import (
    compute_features,
    prepare_m_score_features,   
    detect_anomalies,
    compute_risk_score         
)
from analytics_model import validate_models
from insight_generator import generate_insights
from report_generator import create_charts, generate_report

import time
import json
from datetime import datetime
from groq import Groq
import pandas as pd
import os
import traceback


try:
    from groq import Groq
except ImportError:
    print("ERROR: groq package not installed. Run: pip install groq")
    sys.exit(1)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

client = Groq(api_key="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")
MODEL = "llama-3.3-70b-versatile"

#trace = []

def log(msg, trace):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "message": msg
    }
    trace.append(entry)
    print(f"[{entry['timestamp']}] {msg}")


def log_llm_call(trace,stage, prompt, response, model, usage, latency):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "LLM_CALL",
        "stage": stage,
        "model": model,
        "prompt_preview": prompt[:500],
        "response_preview": response[:1000],
        "token_usage": usage.model_dump() if hasattr(usage, 'model_dump') else vars(usage),
        "latency": latency
    }
    trace.append(entry)


def save_trace(trace,path="output/execution_trace.json"):
    with open(path, "w") as f:
        json.dump(trace, f, indent=2)


def sanitize_for_json(value):
    import math

    if isinstance(value, dict):
        return {k: sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_for_json(v) for v in value]
    if isinstance(value, tuple):
        return [sanitize_for_json(v) for v in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if hasattr(value, "tolist"):
        try:
            return sanitize_for_json(value.tolist())
        except Exception:
            pass
    return value


def append_scenario_to_consolidated(scenario_data, consolidated_path="output/consolidated_analysis.json"):
    """
    Append scenario data to a consolidated JSON file.
    If the file doesn't exist, create it with proper structure.
    """
    try:
        with open(consolidated_path, "r") as f:
            consolidated = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        consolidated = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "total_scenarios": 0,
                "completed_scenarios": 0,
                "failed_scenarios": 0
            },
            "scenarios": []
        }
    
    consolidated["scenarios"].append(scenario_data)
    consolidated["metadata"]["total_scenarios"] = len(consolidated["scenarios"])
    
    # Check status from scenario_metadata
    if scenario_data.get("scenario_metadata", {}).get("status") == "success":
        consolidated["metadata"]["completed_scenarios"] = consolidated["metadata"].get("completed_scenarios", 0) + 1
    else:
        consolidated["metadata"]["failed_scenarios"] = consolidated["metadata"].get("failed_scenarios", 0) + 1
    
    consolidated["metadata"]["last_updated"] = datetime.now().isoformat()
    
    os.makedirs(os.path.dirname(consolidated_path) or ".", exist_ok=True)
    cleaned = sanitize_for_json(consolidated)
    with open(consolidated_path, "w") as f:
        json.dump(cleaned, f, indent=2, allow_nan=False)


def create_consolidated_html_report(consolidated_path="output/consolidated_analysis.json", output_path="output/consolidated_report.html"):
    """
    Create a single consolidated HTML report containing all scenario reports.
    """
    try:
        with open(consolidated_path, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: Could not load consolidated analysis file")
        return
    
    html_parts = []
    
    # HTML Header
    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Consolidated Financial Risk Intelligence Report</title>
<style>
body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f0f4f8;
    margin: 0;
    padding: 20px;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,.08);
    overflow: hidden;
}}

.header {{
    background: linear-gradient(135deg, #1a56db, #1e3a8a);
    color: white;
    padding: 35px;
    text-align: center;
}}

.header h1 {{
    margin: 0;
    font-size: 2.5rem;
}}

.header p {{
    margin: 10px 0 0 0;
    opacity: 0.9;
}}

.scenario-divider {{
    border: 0;
    height: 4px;
    background: linear-gradient(90deg, #1a56db, #1e3a8a);
    margin: 40px 0;
}}

.scenario-header {{
    background: #f8fafc;
    border-left: 6px solid #1a56db;
    padding: 25px;
    margin: 30px 0 20px 0;
}}

.scenario-header h2 {{
    margin: 0 0 10px 0;
    color: #1e3a8a;
    font-size: 1.8rem;
}}

.scenario-header .meta {{
    color: #64748b;
    font-size: 0.9rem;
    margin: 5px 0;
}}

.scenario-header .status {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
    text-transform: uppercase;
}}

.scenario-header .status.success {{
    background: #def7ec;
    color: #065f46;
}}

.scenario-header .status.failed {{
    background: #fde8e8;
    color: #c53030;
}}

.scenario-content {{
    padding: 0 25px 25px 25px;
}}

.footer {{
    background: #f8fafc;
    padding: 25px;
    text-align: center;
    border-top: 1px solid #e2e8f0;
    color: #64748b;
    font-size: 0.9rem;
}}

.summary-stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    padding: 25px;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
}}

.stat-card {{
    text-align: center;
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,.1);
}}

.stat-card .number {{
    font-size: 2rem;
    font-weight: bold;
    color: #1a56db;
}}

.stat-card .label {{
    color: #64748b;
    font-size: 0.9rem;
    text-transform: uppercase;
    margin-top: 5px;
}}
</style>
</head>

<body>
<div class="container">

<div class="header">
<h1>📊 Consolidated Financial Risk Intelligence Report</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>

<div class="summary-stats">
<div class="stat-card">
<div class="number">{data['metadata']['total_scenarios']}</div>
<div class="label">Total Scenarios</div>
</div>
<div class="stat-card">
<div class="number">{data['metadata']['completed_scenarios']}</div>
<div class="label">Completed</div>
</div>
<div class="stat-card">
<div class="number">{data['metadata']['failed_scenarios']}</div>
<div class="label">Failed</div>
</div>
<div class="stat-card">
<div class="number">{len([s for s in data['scenarios'] if s.get('scenario_metadata', {}).get('status') == 'success'])}</div>
<div class="label">Successful</div>
</div>
</div>
""")
    
    # Process each scenario
    for scenario in data['scenarios']:
        metadata = scenario.get('scenario_metadata', {})
        run_id = metadata.get('run_id', 'unknown')
        name = metadata.get('name', 'Unknown Scenario')
        company = metadata.get('company', 'Unknown Company')
        status = metadata.get('status', 'unknown')
        started_at = metadata.get('started_at', 'Unknown')
        completed_at = metadata.get('completed_at') or metadata.get('failed_at', 'Unknown')
        
        # Scenario header
        html_parts.append(f"""
<div class="scenario-header">
<h2>🔍 {name}</h2>
<div class="meta"><strong>Run ID:</strong> {run_id}</div>
<div class="meta"><strong>Company:</strong> {company}</div>
<div class="meta"><strong>Started:</strong> {started_at}</div>
<div class="meta"><strong>Completed:</strong> {completed_at}</div>
<div class="status {status}">{status}</div>
</div>

<hr class="scenario-divider">

<div class="scenario-content">
""")
        
        # Try to read the individual HTML report
        report_path = f"output/{run_id}/report.html"
        if os.path.exists(report_path):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_html = f.read()
                
                # Extract the body content (remove html, head, and body tags)
                # Find content between <body> and </body>
                body_start = report_html.find('<body>')
                body_end = report_html.find('</body>')
                
                if body_start != -1 and body_end != -1:
                    body_content = report_html[body_start + 6:body_end]
                    html_parts.append(body_content)
                else:
                    html_parts.append(f"<p><em>Could not extract report content for {run_id}</em></p>")
                    
            except Exception as e:
                html_parts.append(f"<p><em>Error reading report for {run_id}: {str(e)}</em></p>")
        else:
            if status == 'success':
                html_parts.append(f"<p><em>Report file not found: {report_path}</em></p>")
            else:
                error = metadata.get('error', 'Unknown error')
                html_parts.append(f"<p><em>Scenario failed: {error}</em></p>")
        
        html_parts.append("</div>")  # Close scenario-content
    
    # Footer
    html_parts.append(f"""
<div class="footer">
<p>Report generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
<p>Consolidated analysis from {data['metadata']['total_scenarios']} scenarios</p>
</div>

</div>
</body>
</html>""")
    
    # Write the consolidated HTML
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(html_parts))
    
    print(f"Consolidated HTML report created: {output_path}")


def run_command(cmd, trace, stage_name):
    """Execute a shell command, capture output, and record in trace."""
    log(f"STAGE START: {stage_name}", trace)
    log(f"  Command: {cmd}", trace)

    t0 = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=BASE_DIR)
    elapsed = round(time.time() - t0, 2)

    log(f"  Exit code: {result.returncode} | Duration: {elapsed}s", trace)
    if result.stdout.strip():
        log(f"  STDOUT: {result.stdout.strip()[:500]}", trace)
    if result.stderr.strip():
        log(f"  STDERR: {result.stderr.strip()[:300]}", trace)

    return result.returncode, result.stdout, result.stderr

def load_reference_context():
    try:
        with open("REFERENCE.md", "r") as f:
            return f.read()
    except:
        return "Financial risk analysis using M-score, anomaly detection, and risk scoring."


def llm_generate_financial_insights(client, model, base_insights, trace,company=None):

    prompt = f"""
You are a forensic accounting expert.

Analyze the following financial risk output and generate structured insights for {company}.

INPUT DATA:
{json.dumps(base_insights, indent=2)}

TASK:
1. Interpret overall financial health
2. Explain M-score risk in context
3. Identify hidden risks across metrics
4. Highlight anomaly implications
5. Provide actionable recommendations

Return ONLY valid JSON:

{{
  "executive_summary": "string",
  "risk_analysis": ["string"],
  "m_score_interpretation": "string",
  "anomaly_analysis": "string",
  "key_risks": ["string"],
  "recommendations": ["string"]
}}
"""

    t0 = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a financial fraud detection expert. Use only provided data."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1200
    )

    latency = time.time() - t0
    text = response.choices[0].message.content
    usage = response.usage

    # 🔥 SAME PATTERN AS YOUR FILE
    log_llm_call(
        trace,
        "Stage 6: Financial Insight Generation",
        prompt,
        text,
        model,
        usage,
        latency
    )

    # JSON parsing (same robustness you need)
    try:
        parsed = json.loads(text)
    except:
        parsed = {
            "executive_summary": text,
            "risk_analysis": [],
            "m_score_interpretation": "",
            "anomaly_analysis": "",
            "key_risks": [],
            "recommendations": []
        }

    return parsed
def llm_generate_financial_summary(client, model, insights, trace, company=None):

    prompt = f"""
Write a concise executive summary for a CFO.

INPUT:
{json.dumps(insights, indent=2)}

Focus on {company} and derive a high-level narrative that captures:
- Risk level
- Key drivers
- Urgency
- Actions required
"""

    t0 = time.time()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )

    latency = time.time() - t0
    text = response.choices[0].message.content

    log_llm_call(
        trace,
        "Stage 7: Executive Summary",
        prompt,
        text,
        model,
        response.usage,
        latency
    )

    return text

SCENARIOS = [
    {
        "run_id": "run1_normal",
        "name": "Run 1: Clean Dataset",
        "data_path": "data/financial_table.csv",
        "prompt": "Analyze the financial risk for  CIK 3453 (MATSON, INC.)  using the default dataset. Use a lookback period of 4 quarters and flag anything above a risk threshold of 65. I need a full report with all charts and a business interpretation.",
        "company": "CIK 3453 (MATSON, INC.)"
    },
    {
        "run_id": "run2_stressed",
        "name": "Run 2: High Risk Scenario",
        "data_path": "data/financial_high_risk.csv",
        "prompt": "Run a risk assessment on CIK 58361(Lee Enterprises Inc.) using the default dataset. Use defaults for lookback (3 periods) and risk threshold (70). I want to understand why this company is flagged as risky and what the models agree on.",
        "company": "CIK 58361 (Lee Enterprises Inc.)"
    },
    {
        "run_id": "run3_bad_data",
        "name": "Run 3: Bad Data (Expected Failure)",
        "data_path": "data/financial_bad_data.csv",
        "prompt": "Analyze financial risk for CIK 2267 using this dataset I'm uploading. Just give me the risk score.",
        "company": "CIK 2267"
    },
      {
        "run_id": "run4_manipulated_data",
        "name": "Run 4: Manipulated Data (Advanced Analysis)",
        "data_path": "data/financial_manipulated_data.csv",
        "prompt": "Run a risk assessment on CIK 1844505(QT Imaging Holdings Inc.) using the default dataset. Use defaults for lookback (3 periods) and risk threshold (70). I want to understand if there is a posibility of numbers manipulation for this firm.",
        "company": "CIK 1844505(QT Imaging Holdings Inc.)"
    }
]
def generate_failure_report(quality, run_dir, scenario, trace):

    html = f"""
    <html>
    <body>
    <h1>Pipeline Failure</h1>
    <p>Scenario: {scenario['name']}</p>
    <p>Errors: {quality.get('errors')}</p>
    </body>
    </html>
    """

    with open(f"{run_dir}/failure_report.html", "w") as f:
        f.write(html)

    log("Failure report generated", trace)
def run_scenario(scenario, client, model):

    run_dir = f"output/{scenario['run_id']}"
    os.makedirs(run_dir, exist_ok=True)

    trace = []
    log(f"PIPELINE RUN: {scenario['name']}", trace)
    
    scenario_start_time = datetime.now().isoformat()

    try:
        # -----------------------------
        # Stage 0: Load Data
        # -----------------------------
        df = pd.read_csv(scenario["data_path"])
        df['ddate'] = pd.to_datetime(df['ddate'])

        # -----------------------------
        # Stage 1: Validation
        # -----------------------------
        validation_result = run_validation(df)
        if validation_result['status'] != 'success':
            raise Exception(f"Validation failed: {validation_result}")

        # -----------------------------
        # Stage 2: Features
        # -----------------------------
        df_features = compute_features(df)
        df_features = prepare_m_score_features(df_features)

        # -----------------------------
        # Stage 3: Anomaly
        # -----------------------------
        df_anomaly = detect_anomalies(df_features, df_features)

        latest = df_anomaly.iloc[-1]

        anomaly_signal = {
            "is_anomaly": int(latest['anomaly_flag'] == -1),
            "anomaly_score": float(latest['anomaly_score'])
        }

        # -----------------------------
        # Stage 4: Risk
        # -----------------------------
        score, drivers = compute_risk_score(df_anomaly)

        # -----------------------------
        # Stage 5: Validation
        # -----------------------------
        validation = validate_models(df_anomaly, score)

        # -----------------------------
        # Stage 6: Base Insights
        # -----------------------------
        base_insights = generate_insights(
            df_anomaly, score, drivers, validation, anomaly_signal
        )

        # -----------------------------
        # Stage 7: LLM Insights
        # -----------------------------
        llm_insights = llm_generate_financial_insights(
            client, model, base_insights, trace, company=scenario["company"]
        )

        # Also save to run-specific directory for backward compatibility
        with open(f"{run_dir}/llm_insights.json", "w") as f:
            json.dump(llm_insights, f, indent=2)

        # -----------------------------
        # Stage 8: Executive Summary
        # -----------------------------
        llm_summary = llm_generate_financial_summary(
            client, model, llm_insights, trace, company=scenario["company"]
        )

        with open(f"{run_dir}/llm_summary.txt", "w") as f:
            f.write(llm_summary)

        # Also save to run-specific directory for backward compatibility
        with open(f"{run_dir}/execution_trace.json", "w") as f:
            json.dump(trace, f, indent=2)

        # -----------------------------
        # Final Merge
        # -----------------------------
        final_insights = {
            **base_insights,
            "llm_insights": llm_insights,
            "executive_summary": llm_summary
        }
        

        # -----------------------------
        # Stage 9: Report
        # -----------------------------
        create_charts(df_anomaly)
        generate_report(scenario["prompt"],scenario["run_id"], df_anomaly, final_insights, validation)

        log("PIPELINE COMPLETE", trace)

        # ========== CONSOLIDATE SCENARIO DATA ==========
        scenario_end_time = datetime.now().isoformat()
        scenario_data = {
            "scenario_metadata": {
                "run_id": scenario["run_id"],
                "name": scenario["name"],
                "company": scenario["company"],
                "data_source": scenario["data_path"],
                "status": "success",
                "started_at": scenario_start_time,
                "completed_at": scenario_end_time
            },
            "execution_trace": trace,
            "llm_insights": llm_insights,
            "llm_summary": llm_summary,
            "Intermediate_output": llm_summary,
            "base_insights": base_insights,
            "validation": validation
        }
        
        # Save to consolidated output
        append_scenario_to_consolidated(scenario_data)

        return True
   

    except Exception as e:
        log(f"PIPELINE FAILED: {str(e)}", trace)
        log(traceback.format_exc(), trace)

        # Still save trace to run-specific directory for debugging
        with open(f"{run_dir}/execution_trace.json", "w") as f:
            json.dump(trace, f, indent=2)

        generate_failure_report(
            {"errors": [str(e)], "warnings": []},
            run_dir,
            scenario,
            trace
        )

        # ========== CONSOLIDATE FAILURE DATA ==========
        scenario_end_time = datetime.now().isoformat()
        scenario_data = {
            "scenario_metadata": {
                "run_id": scenario["run_id"],
                "name": scenario["name"],
                "company": scenario["company"],
                "data_source": scenario["data_path"],
                "status": "failed",
                "error": str(e),
                "started_at": scenario_start_time,
                "failed_at": scenario_end_time
            },
            "execution_trace": trace,
            "llm_insights": None,
            "llm_summary": None,
            "Intermediate_output": None,
            "base_insights": None,
            "validation": None
        }
        
        # Save to consolidated output
        append_scenario_to_consolidated(scenario_data)

        return False
def main():

    consolidated_path = "output/consolidated_analysis.json"
    consolidated_html_path = "output/consolidated_report.html"
    if os.path.exists(consolidated_path):
        os.remove(consolidated_path)
    if os.path.exists(consolidated_html_path):
        os.remove(consolidated_html_path)

    client = Groq(api_key="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")
    model = "llama-3.3-70b-versatile"

    summary = []
    program_start = datetime.now().isoformat()

    for scenario in SCENARIOS:

        success = run_scenario(scenario, client, model)

        summary.append({
            "run_id": scenario["run_id"],
            "name": scenario["name"],
            "success": success
        })

    program_end = datetime.now().isoformat()

    # Save summary to both traditional summary and update consolidated
    run_summary = {
        "program_execution": {
            "started_at": program_start,
            "completed_at": program_end,
            "total_scenarios": len(SCENARIOS),
            "successful_scenarios": sum(1 for s in summary if s["success"]),
            "failed_scenarios": sum(1 for s in summary if not s["success"])
        },
        "scenario_results": summary
    }
    
    with open("output/run_summary.json", "w") as f:
        json.dump(run_summary, f, indent=2)
    
    # Create consolidated HTML report
    create_consolidated_html_report()
    
    print(f"\n{'='*60}")
    print("EXECUTION COMPLETE")
    print(f"{'='*60}")
    print(">> Consolidated Analysis: output/consolidated_analysis.json")
    print(">> Consolidated HTML Report: output/consolidated_report.html")
    print(">> Run Summary: output/run_summary.json")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
    
