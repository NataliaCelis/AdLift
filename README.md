# End-to-End A/B Testing & Experimentation Platform (v2: Ad Lift Study)

Full pipeline for a real ad-effectiveness A/B test: experiment design →
data modeling (dbt/Snowflake) → statistical analysis (Python) → BI-ready
exports (Tableau/Looker Studio)

**Dataset:** Kaggle's "Marketing A/B Testing" dataset (`marketing_AB.csv`,
588,101 rows; `user id, test group, converted, total ads, most ads day,
most ads hour`) - a real ad-exposure vs. PSA-holdout conversion-lift study,
the same design methodology Meta and Google Ads use to measure ad
incrementality.

## Bottom line
Users shown the ad converted at 2.56% vs. 1.79% for the PSA
holdout
A **+43.1% relative lift**, p < 0.0001 (z-test, chi-square, and a
10,000-resample bootstrap all agree). The lift is positive on every single
day of the week and shows a clean monotonic dose-response (more ad exposure
→ higher conversion), which is strong evidence this is a real causal effect,
not noise.

## How to run it end-to-end

```
pip install pandas numpy scipy statsmodels matplotlib

python scripts/01_experiment_design.py      # power analysis for unequal allocation
python scripts/02_data_cleaning.py          # data quality checks (dataset is already clean)
python scripts/03_statistical_analysis.py   # exposure balance, z-test, chi-sq, bootstrap, dose-response, figures
python scripts/04_dashboard_exports.py      # flat CSVs for Tableau / Looker Studio

cd memo && node build_memo.js               # builds results_memo.docx
```

## Folder guide

```
data/
  marketing_ab_raw.csv       raw dataset as downloaded (588,101 rows)
  marketing_ab_clean.csv     standardized column names/types (no rows removed)

scripts/
  01_experiment_design.py     hypothesis, guardrails, power analysis for unequal allocation
  02_data_cleaning.py         null/duplicate/category checks, exposure-balance sanity check
  03_statistical_analysis.py  z-test, chi-sq, bootstrap, dose-response, day-of-week stability
  04_dashboard_exports.py     PM-facing CSVs for BI tools + illustrative revenue estimate

dbt/                          dbt project targeting Snowflake
  dbt_project.yml
  profiles.yml.example        copy to ~/.dbt/profiles.yml, fill in your Snowflake creds
  load_raw_data_snowflake.sql one-time raw table setup / COPY INTO
  models/staging/stg_ad_events.sql          typed passthrough + defensive dedupe
  models/marts/dim_users.sql                1 row per user + exposure bucket
  models/marts/fct_conversions.sql          BI-ready fact table
  models/marts/agg_daily_conversion.sql     daily trend, by group
  models/marts/agg_dose_response.sql        conversion by exposure decile
  models/marts/agg_experiment_summary.sql   topline KPIs table
  tests/assert_exposure_balance.sql         custom guardrail: exposure-opportunity balance
  models/marts/_schema.yml    dbt tests: unique/not_null/accepted_values/range

exports/                      generated outputs
  experiment_design.json      power analysis results
  data_quality_report.json    cleaning/validation stats
  results.json                full statistical readout (source of truth for memo)
  dash_topline_summary.csv    1-row KPI scorecard -> Tableau/Looker Studio
  dash_daily_conversion.csv   daily trend by group -> line/bar chart
  dash_hourly_conversion.csv  hour-of-day x group -> heatmap
  dash_dose_response.csv      exposure decile x conversion -> line chart
  dash_user_level.csv         row-level fact table -> filters/pivots
  dash_bootstrap_samples.csv  5,000 bootstrap lift draws -> histogram

figures/                      PNG charts (also embedded in the memo)
memo/
  build_memo.js                generates the docx from exports/results.json
  results_memo.docx            final one-page ship/no-ship memo
```

## Loading into Tableau / Looker Studio
Import the `dash_*.csv` files from `exports/` as separate data sources.
`dash_topline_summary.csv` drives scorecards, `dash_daily_conversion.csv`
the day-of-week stability chart, `dash_dose_response.csv` the exposure
curve, and `dash_bootstrap_samples.csv` a histogram of the lift so a PM can
see the uncertainty, not just the point estimate.

## Loading into Snowflake / running dbt
1. Run `dbt/load_raw_data_snowflake.sql` in a Snowflake worksheet (or upload
   `data/marketing_ab_clean.csv` via Snowsight's "Load Data" UI) to populate
   `AD_LIFT.RAW.AD_EVENTS`.
2. `cp dbt/profiles.yml.example ~/.dbt/profiles.yml` and fill in your
   Snowflake account/user/password (free trial: signup.snowflake.com).
3. `cd dbt && dbt deps && dbt run && dbt test`.

## Revenue estimate caveat
This dataset has no order-value field, so `dash_topline_summary.csv` and the
memo compute incremental revenue using a **$50 AOV assumption.** Swap in your real average order
value before using the revenue number anywhere it matters!
