"""
04_dashboard_exports.py

Flat CSVs shaped for Tableau/Looker Studio import.

Note on revenue: this dataset has no order-value field, so any $ revenue
estimate requires an assumed average order value (AOV). We compute it
explicitly with a clearly-labeled, adjustable assumption rather than
presenting a single made-up number as fact.
"""
import json
import numpy as np
import pandas as pd

CLEAN_PATH = "/home/claude/marketing_ab_project/data/marketing_ab_clean.csv"
RESULTS_PATH = "/home/claude/marketing_ab_project/exports/results.json"
EXPORT_DIR = "/home/claude/marketing_ab_project/exports"

np.random.seed(42)
ASSUMED_AOV = 50  # <-- illustrative assumption, clearly labeled; adjust to real AOV

df = pd.read_csv(CLEAN_PATH)
df["converted"] = df["converted"].astype(bool)

with open(RESULTS_PATH) as f:
    results = json.load(f)

topline = results["topline"]
alloc = results["allocation_guardrail"]
z = results["z_test"]
rec = results["recommendation"]

# --- 1. Topline summary (1 row, scorecard) ---------------------------------
incremental_conversions = topline["incremental_conversions"]
summary_row = {
    "n_ad": topline["n_ad"],
    "n_psa": topline["n_psa"],
    "psa_holdout_pct": alloc["psa_holdout_pct"],
    "conversion_rate_ad_pct": round(topline["conversion_rate_ad"] * 100, 3),
    "conversion_rate_psa_pct": round(topline["conversion_rate_psa"] * 100, 3),
    "absolute_lift_pp": topline["absolute_lift_pp"],
    "relative_lift_pct": topline["relative_lift_pct"],
    "lift_ci95_lower_pp": topline["absolute_lift_ci95_pp"][0],
    "lift_ci95_upper_pp": topline["absolute_lift_ci95_pp"][1],
    "p_value": z["p_value"],
    "statistically_significant": z["significant_at_0.05"],
    "incremental_conversions": incremental_conversions,
    "assumed_aov_usd": ASSUMED_AOV,
    "estimated_incremental_revenue_usd": incremental_conversions * ASSUMED_AOV,
    "recommendation": rec["recommendation"],
}
pd.DataFrame([summary_row]).to_csv(f"{EXPORT_DIR}/dash_topline_summary.csv", index=False)

# --- 2. Conversion by day of week -------------------------------------------
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
daily = (
    df.groupby(["most ads day" if "most ads day" in df.columns else "most_ads_day", "test group" if "test group" in df.columns else "test_group"])["converted"]
    .agg(users="count", conversions="sum", conversion_rate="mean")
    .reset_index()
)
daily.columns = ["most_ads_day", "test_group", "users", "conversions", "conversion_rate"]
daily["most_ads_day"] = pd.Categorical(daily["most_ads_day"], categories=day_order, ordered=True)
daily = daily.sort_values("most_ads_day")
daily["conversion_rate_pct"] = daily["conversion_rate"] * 100
daily.to_csv(f"{EXPORT_DIR}/dash_daily_conversion.csv", index=False)

# --- 3. Conversion by hour of day x group -----------------------------------
hourly = (
    df.groupby(["most_ads_hour", "test_group"])["converted"]
    .agg(users="count", conversion_rate="mean")
    .reset_index()
)
hourly["conversion_rate_pct"] = hourly["conversion_rate"] * 100
hourly.to_csv(f"{EXPORT_DIR}/dash_hourly_conversion.csv", index=False)

# --- 4. Dose-response (exposure decile x conversion, ad group only) --------
ad_df = df[df["test_group"] == "ad"].copy()
ad_df["exposure_decile"] = pd.qcut(ad_df["total_ads"], 10, labels=False, duplicates="drop") + 1
dose = (
    ad_df.groupby("exposure_decile")
    .agg(mean_total_ads=("total_ads", "mean"), users=("converted", "size"), conversion_rate=("converted", "mean"))
    .reset_index()
)
dose["conversion_rate_pct"] = dose["conversion_rate"] * 100
dose.to_csv(f"{EXPORT_DIR}/dash_dose_response.csv", index=False)

# --- 5. Row-level fact table (filters/pivots in Tableau) -------------------
user_level = df[["user_id", "test_group", "total_ads", "most_ads_day", "most_ads_hour", "converted"]].copy()
user_level.to_csv(f"{EXPORT_DIR}/dash_user_level.csv", index=False)

# --- 6. Bootstrap lift draws (histogram) ------------------------------------
ad_arr = df[df["test_group"] == "ad"]["converted"].astype(int).values
psa_arr = df[df["test_group"] == "psa"]["converted"].astype(int).values
N_BOOT = 5000
boot_lifts = np.empty(N_BOOT)
for i in range(N_BOOT):
    a = np.random.choice(ad_arr, size=len(ad_arr), replace=True)
    p = np.random.choice(psa_arr, size=len(psa_arr), replace=True)
    boot_lifts[i] = (a.mean() - p.mean()) * 100
pd.DataFrame({"resample_id": range(N_BOOT), "lift_pp": boot_lifts}).to_csv(
    f"{EXPORT_DIR}/dash_bootstrap_samples.csv", index=False
)

print("Dashboard export files written to", EXPORT_DIR)
import os
for fn in [
    "dash_topline_summary.csv", "dash_daily_conversion.csv", "dash_hourly_conversion.csv",
    "dash_dose_response.csv", "dash_user_level.csv", "dash_bootstrap_samples.csv"
]:
    path = f"{EXPORT_DIR}/{fn}"
    print(f"  {fn}: {os.path.getsize(path)/1024:.1f} KB")
