"""
02_data_cleaning.py

The raw marketing_AB.csv is already clean (no nulls, no duplicate users), but
we still run the standard checks a real pipeline would run, and standardize
column names/types for downstream use.
"""
import json
import pandas as pd

RAW_PATH = "/home/claude/marketing_ab_project/data/marketing_ab_raw.csv"
CLEAN_PATH = "/home/claude/marketing_ab_project/data/marketing_ab_clean.csv"
DQ_REPORT_PATH = "/home/claude/marketing_ab_project/exports/data_quality_report.json"

df = pd.read_csv(RAW_PATH)
n_raw = len(df)

df = df.rename(columns={
    "user id": "user_id",
    "test group": "test_group",
    "total ads": "total_ads",
    "most ads day": "most_ads_day",
    "most ads hour": "most_ads_hour",
})
df = df.drop(columns=["Unnamed: 0"], errors="ignore")

report = {
    "rows_raw": n_raw,
    "null_counts": df.isna().sum().to_dict(),
    "duplicate_user_ids": int(df["user_id"].duplicated().sum()),
    "invalid_test_group_values": int((~df["test_group"].isin(["ad", "psa"])).sum()),
    "invalid_hour_range": int((~df["most_ads_hour"].between(0, 23)).sum()),
    "total_ads_min": int(df["total_ads"].min()),
    "total_ads_max": int(df["total_ads"].max()),
    "rows_clean_final": n_raw,  # nothing needed removal
    "group_counts": df["test_group"].value_counts().to_dict(),
    "exposure_balance_check": {
        "note": "Mean 'total_ads' (ad-slot impressions) by group - should be "
                "similar across arms if the ad/PSA swap was randomized at the "
                "impression level, independent of the intentional group-size "
                "imbalance.",
        "mean_total_ads_by_group": df.groupby("test_group")["total_ads"].mean().round(3).to_dict(),
    },
}

print(json.dumps(report, indent=2))

df.to_csv(CLEAN_PATH, index=False)
with open(DQ_REPORT_PATH, "w") as f:
    json.dump(report, f, indent=2)

print(f"\nSaved clean dataset ({len(df):,} rows) to {CLEAN_PATH}")
