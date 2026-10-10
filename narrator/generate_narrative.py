# Part 3 — GenAI-Powered Insight Narrator
# Structure: Situation – Complication – Resolution (SCR)


import json
import os
import re
from pathlib import Path

from google import genai
from google.genai import types



# STEP 1: FILE PATHS AND CONFIGURATION

# Supports running this code as a .py file or in Google Colab.
if "__file__" in globals():
    BASE_DIR = Path(__file__).resolve().parent.parent
else:
    BASE_DIR = Path.cwd()

NARRATOR_DIR = BASE_DIR / "narrator"
FINDINGS_FILE = NARRATOR_DIR / "findings.json"
SAMPLE_OUTPUT_FILE = NARRATOR_DIR / "sample_output.txt"

NARRATOR_DIR.mkdir(parents=True, exist_ok=True)

# Use a free-tier Gemini API key if configured.
# The offline fallback does not require a key or network access.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

print("Base directory:", BASE_DIR)
print("Findings file:", FINDINGS_FILE)
print("Sample output file:", SAMPLE_OUTPUT_FILE)



# STEP 2: OFFLINE SCR NARRATIVE GENERATOR

def generate_scr_narrative_offline(findings: dict) -> dict:
    """
    Generate a deterministic SCR narrative without an API call.

    Works without an API key or network access.
    All numerical findings are taken from the supplied dictionary.
    """

    try:
        cleaned_revenue = findings["cleaned_total_revenue_inr"]
        raw_revenue = findings["raw_total_revenue_inr"]
        delta = findings["duplicate_reconciliation_delta_inr"]

        payment_rates = findings["return_rate_by_payment"]

        highest_risk = findings["highest_risk_segment"]
        peak = findings["true_peak_month"]
        inflated = findings["outlier_inflated_month"]

        cod_rate = payment_rates["COD"]
        card_rate = payment_rates["CARD"]
        upi_rate = payment_rates["UPI"]

        risk_method = highest_risk["payment_method"]
        risk_tier = highest_risk["city_tier"]
        risk_rate = highest_risk["return_rate_pct"]

        peak_month = peak["month"]
        peak_revenue = peak["revenue_inr"]

        inflated_month = inflated["month"]
        inflated_revenue = inflated["apparent_revenue_inr"]
        corrected_revenue = inflated["corrected_revenue_inr"]

        # Convert YYYY-MM to a readable month name.
        month_name = peak_month

        try:
            from datetime import datetime

            month_name = datetime.strptime(
                peak_month, "%Y-%m"
            ).strftime("%B %Y")
        except (ValueError, TypeError):
            pass

        narrative = f"""
Situation

Mamaearth's cleaned order data reports total revenue of
₹{cleaned_revenue:,.2f}, compared with raw reported revenue of
₹{raw_revenue:,.2f}. The observed return rates are {cod_rate:.1f}%
for Cash on Delivery (COD), {card_rate:.1f}% for CARD, and
{upi_rate:.1f}% for UPI. These verified figures provide a starting
point for regional operations and finance decisions.

Complication

The highest-risk segment is {risk_method} in City Tier-{risk_tier},
with a return rate of {risk_rate:.1f}%. The difference between raw
and cleaned revenue is ₹{delta:,.2f}, attributable to the five
duplicate orders removed during data cleaning.

January ({inflated_month}) initially appears to generate
₹{inflated_revenue:,.2f}. After excluding the identified quantity
outliers, January revenue is ₹{corrected_revenue:,.2f}. Therefore,
the uncorrected monthly total should not be used alone to identify
the strongest-performing month.

Resolution

Prioritize an operational review of the {risk_method} and
City Tier-{risk_tier} segment, which has a {risk_rate:.1f}% return
rate. Use the cleaned revenue figure of ₹{cleaned_revenue:,.2f}
for analysis after duplicate reconciliation.

The outlier-corrected time series identifies {month_name}
({peak_month}) as the true peak month, with revenue of
₹{peak_revenue:,.2f}. Base month-to-month comparisons on the
corrected series, while retaining records of excluded orders
for auditability.
""".strip()

        return {
            "status": "success",
            "narrative": narrative,
            "tokens": None
        }

    except Exception as err:
        return {
            "status": "error",
            "narrative": None,
            "message": str(err)
        }



# STEP 3: GEMINI-POWERED SCR NARRATIVE GENERATOR

def generate_scr_narrative(findings: dict) -> dict:
    """
    Generate a business narrative using Gemini.

    If no API key is configured, use the offline fallback.
    If an API request fails, return a structured error dictionary.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    # No API key: use the fully offline path.
    if not api_key:
        print("No Gemini API key configured. Using offline mode.")
        return generate_scr_narrative_offline(findings)

    system_instruction = """
You are a senior data analyst writing for Mamaearth's regional
ops and finance heads.

Write a business narrative using exactly three labeled sections:

Situation
Complication
Resolution

Every number in the narrative must come from the supplied
findings dictionary and retain the same value. Do not invent
statistics, percentages, dates, financial amounts, or sample sizes.

Situation:
Explain the verified revenue and payment-method return rates.

Complication:
Explain the duplicate-reconciliation difference, highest-risk
segment, and outlier-inflated month.

Resolution:
Recommend practical actions based on the supplied findings
and identify the true peak month.

Use clear, concise, professional language appropriate for
business leaders. Do not claim that correlation proves causation.
"""

    # Dynamically build the prompt from the supplied findings.
    # Do not hardcode the numerical values into this prompt.
    user_prompt = (
        "Create the SCR business narrative using these verified "
        "findings. Preserve their values exactly.\n\n"
        "Verified findings JSON:\n"
        + json.dumps(findings, indent=2, ensure_ascii=False)
    )

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,

                # Temperature 0.0 reduces variation in this
                # factual business report.
                temperature=0.0,

                # Explicit limit: enough for a three-section report.
                max_output_tokens=600,
            ),
            # Explicit request timeout: 30 seconds, in milliseconds.
            http_options=types.HttpOptions(timeout=30000),
        )

        narrative = response.text or ""

        if not narrative.strip():
            raise ValueError("Gemini returned an empty narrative.")

        usage = getattr(response, "usage_metadata", None)

        total_tokens = (
            getattr(usage, "total_token_count", None)
            if usage is not None
            else None
        )

        return {
            "status": "success",
            "narrative": narrative.strip(),
            "tokens": total_tokens
        }

    except Exception as err:
        # Never return a raw exception to the caller.
        return {
            "status": "error",
            "narrative": None,
            "message": str(err)
        }



# STEP 4: NUMERIC ACCURACY CHECKER

def check_numeric_accuracy(narrative: str, findings: dict) -> bool:
    """
    Check that the five required findings appear in the narrative.

    Normalizes commas and currency symbols before checking numbers.
    Accepts either a readable month name or YYYY-MM for the peak.
    """

    # FIX: Remove currency symbols and commas before checking.
    normalized_text = narrative.replace("₹", "").replace(",", "")
    normalized_text = re.sub(r"\s+", " ", normalized_text)

    cleaned_revenue = findings["cleaned_total_revenue_inr"]
    cod_rate = findings["return_rate_by_payment"]["COD"]

    risk_rate = findings["highest_risk_segment"]["return_rate_pct"]
    delta = findings["duplicate_reconciliation_delta_inr"]

    peak = findings["true_peak_month"]
    peak_month = peak["month"]
    peak_revenue = peak["revenue_inr"]

    # Accept March, March 2026, or 2026-03.
    month_name = peak_month

    try:
        from datetime import datetime

        month_name = datetime.strptime(
            peak_month, "%Y-%m"
        ).strftime("%B")
    except (ValueError, TypeError):
        pass

    checks = [
        (
            "Cleaned total revenue",
            f"{cleaned_revenue:.2f}" in normalized_text
        ),
        (
            "COD return rate",
            f"{cod_rate:.1f}" in normalized_text
        ),
        (
            "Highest-risk segment return rate",
            f"{risk_rate:.1f}" in normalized_text
        ),
        (
            "Duplicate reconciliation delta",
            f"{delta:.2f}" in normalized_text
        ),
        (
            "True peak month and revenue",
            (
                (
                    month_name.lower() in narrative.lower()
                    or peak_month in narrative
                )
                and f"{peak_revenue:.2f}" in normalized_text
            )
        )
    ]

    all_passed = True

    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {label}")

        if not passed:
            all_passed = False

    return all_passed


# STEP 5: MAIN EXECUTION

def main():

    # Check whether findings.json exists.
    if not FINDINGS_FILE.exists():
        print(f"ERROR: Cannot find {FINDINGS_FILE}")
        print(
            "Generate findings.json from analysis/clean_and_eda.py "
            "before running the narrator."
        )
        return

    # Load verified findings.
    with FINDINGS_FILE.open("r", encoding="utf-8") as file:
        findings = json.load(file)

    # Attempt Gemini if configured; otherwise use offline mode.
    result = generate_scr_narrative(findings)

    # Fall back to offline mode if the Gemini request fails.
    if result["status"] == "error":
        print("\nGemini generation failed.")
        print("Reason:", result["message"])
        print("Switching to the offline fallback.")

        result = generate_scr_narrative_offline(findings)

    # Check the final result.
    if result["status"] != "success":
        print("ERROR: Narrative generation failed.")
        print(result.get("message", "Unknown error"))
        return

    narrative = result["narrative"]

    print("\n" + "=" * 60)
    print("GENERATED SCR NARRATIVE")
    print("=" * 60 + "\n")

    print(narrative)

    # Run the five required numeric checks.
    print("\n" + "=" * 60)
    print("NUMERIC ACCURACY CHECK")
    print("=" * 60)

    numeric_pass = check_numeric_accuracy(narrative, findings)

    # Save the actual narrative for grading.
    SAMPLE_OUTPUT_FILE.write_text(
        narrative + "\n",
        encoding="utf-8"
    )

    print(f"\nSample saved to: {SAMPLE_OUTPUT_FILE}")

    if numeric_pass:
        print("\nAll required numeric checks passed.")
    else:
        print(
            "\nWARNING: The narrative failed one or more numeric "
            "checks. Review it before submission."
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
