from groq import Groq
import json
import os
import re

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"


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


def normalize_llm_response(text):
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = re.sub(r"^json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^#+\s*JSON Response:?.*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip()


def generate_llm_narrative(prompt, insights, validation, features_tail):
    """
    Generates executive narrative using LLM
    """

    prompt = f"""
You are a financial risk analyst.

{prompt}

RISK DATA:
{json.dumps(insights, indent=2)}

VALIDATION:
{json.dumps(validation, indent=2)}

LATEST FEATURES:
{features_tail.to_dict()}

Return only a valid JSON object containing:
- executive_summary (short paragraph)
- key_drivers (array of strings)
- risk_outlook (string)
- red_flags (array of strings)
- recommendations (array of strings)

Do not include any markdown, headings, or explanatory text outside the JSON object.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    raw_text = response.choices[0].message.content or ""
    cleaned_text = normalize_llm_response(raw_text)

    try:
        return json.loads(cleaned_text)
    except Exception:
        pass

    candidate = extract_json_object(cleaned_text) or extract_json_object(raw_text)
    if candidate:
        try:
            return json.loads(candidate)
        except Exception:
            pass

    fallback = re.sub(r"^#+\s*", "", cleaned_text, flags=re.MULTILINE)
    fallback = re.sub(r"[`*\"]", "", fallback)
    fallback = re.sub(r"JSON Response:.*", "", fallback, flags=re.IGNORECASE | re.DOTALL).strip()

    return {
        "executive_summary": fallback or "No narrative generated.",
        "key_drivers": [],
        "risk_outlook": "",
        "red_flags": [],
        "recommendations": []
    }
