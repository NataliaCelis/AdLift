-- Guardrail test: fails the dbt run if ad-slot exposure opportunity
-- ('total_ads') differs meaningfully between the ad and PSA arms. Since
-- this is an intentional PSA-holdout design (not a 50/50 split), a plain
-- sample-ratio-mismatch check doesn't apply - the real risk here is that
-- the ad/PSA swap wasn't randomized independently of how much a user
-- browses. A large gap in mean total_ads between arms would indicate that
-- confound.
-- Threshold: fails if the two arms' mean total_ads differ by more than 10%
-- relative to the smaller of the two means.

with summary as (
    select * from {{ ref('agg_experiment_summary') }}
),

check_balance as (
    select
        mean_ads_psa,
        mean_ads_ad,
        abs(mean_ads_ad - mean_ads_psa) / least(mean_ads_ad, mean_ads_psa) as pct_diff
    from summary
)

select *
from check_balance
where pct_diff > 0.10
