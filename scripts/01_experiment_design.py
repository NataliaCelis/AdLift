"""
01_experiment_design.py

This is a classic "ad lift" / "conversion lift" study design (the same
methodology Meta and Google Ads use): most users are shown the real ad,
while a smaller PSA holdout group is shown a public service announcement
in the same ad slot instead. The holdout is intentionally small (~4% here)
because withholding ads from a large share of users is expensive for the
business - but it needs to be large enough to detect a real effect.

We pre-register the hypothesis/metrics, then run a power analysis for an
*unequal-allocation* two-proportion test (ratio = n_psa / n_ad), and check
whether the actual holdout size was big enough.
"""
import json
import numpy as np
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

OUT_PATH = "/home/claude/marketing_ab_project/exports/experiment_design.json"

# ---------------------------------------------------------------------------
# 1. Design parameters
# ---------------------------------------------------------------------------
BASELINE_CVR = 0.018          # ~observed historical baseline (PSA/no-ad conversion)
MDE_RELATIVE = 0.15           # Minimum detectable effect: +15% relative lift
TARGET_CVR = BASELINE_CVR * (1 + MDE_RELATIVE)
ALPHA = 0.05
POWER = 0.80
ACTUAL_RATIO = 23524 / 564577  # n_psa / n_ad actually observed in the data

hypothesis = {
    "design": "Ad exposure lift study (PSA holdout design) - most users see the "
               "real ad; a smaller randomized holdout sees a public service "
               "announcement (PSA) in the same slot instead of the ad. This "
               "isolates the causal/incremental effect of the ad itself.",
    "null_hypothesis": "H0: Conversion rate is equal whether a user is shown the "
                        "ad or the PSA (p_ad = p_psa).",
    "alt_hypothesis": "H1: Conversion rate differs between ad and PSA (p_ad != p_psa). "
                       "Two-sided test; directionally we expect ads to lift conversion.",
    "primary_metric": "converted (binary): whether the user completed a purchase.",
    "guardrail_metrics": [
        "Exposure-opportunity balance: 'total ads' (ad-slot impressions) should "
        "have a similar distribution in both arms, confirming the ad/PSA swap "
        "was randomized at the impression level and not confounded by which "
        "users happened to browse more.",
        "Holdout size adequacy: is the (intentionally small) PSA group still "
        "large enough to reach the pre-registered power?",
        "Dose-response sanity check: conversion should trend upward with more "
        "ad exposure within the ad group, consistent with a real causal effect "
        "rather than noise.",
    ],
}

# ---------------------------------------------------------------------------
# 2. Power analysis for the ACTUAL (unequal) allocation ratio
# ---------------------------------------------------------------------------
effect_size = proportion_effectsize(TARGET_CVR, BASELINE_CVR)
analysis = NormalIndPower()

# Required n in the smaller (psa) arm, given ratio = n_ad/n_psa in statsmodels' convention
# statsmodels ratio = n2/n1; solve for n1 (psa, the smaller/control arm), n2 = n1/ACTUAL_RATIO... 
# simpler: solve assuming this actual ratio of psa:ad
ratio_ad_to_psa = 1 / ACTUAL_RATIO  # ad is much larger than psa
n_psa_required = analysis.solve_power(
    effect_size=effect_size, alpha=ALPHA, power=POWER,
    ratio=ratio_ad_to_psa, alternative="two-sided"
)
n_psa_required = int(np.ceil(n_psa_required))
n_ad_required = int(np.ceil(n_psa_required * ratio_ad_to_psa))

design = {
    "hypothesis": hypothesis,
    "power_analysis": {
        "baseline_conversion_rate": BASELINE_CVR,
        "mde_relative_pct": MDE_RELATIVE * 100,
        "target_conversion_rate": round(TARGET_CVR, 5),
        "alpha": ALPHA,
        "power": POWER,
        "actual_allocation_ratio_psa_to_ad": round(ACTUAL_RATIO, 4),
        "cohens_h_effect_size": round(effect_size, 4),
        "required_n_psa_holdout": n_psa_required,
        "required_n_ad": n_ad_required,
        "actual_n_psa_holdout": 23524,
        "actual_n_ad": 564577,
        "holdout_adequately_powered": bool(23524 >= n_psa_required),
    },
}

print(json.dumps(design, indent=2))
with open(OUT_PATH, "w") as f:
    json.dump(design, f, indent=2)

print(f"\n>>> Required PSA holdout size for +{MDE_RELATIVE*100:.0f}% relative MDE at "
      f"alpha={ALPHA}, power={POWER}: {n_psa_required:,}. "
      f"Actual holdout: 23,524 -> {'ADEQUATE' if 23524 >= n_psa_required else 'UNDERPOWERED'}.")
