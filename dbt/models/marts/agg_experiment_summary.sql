-- Single-row topline summary: sample sizes, conversion rates, lift.
-- Powers the PM scorecard. p-values/CIs are computed in Python
-- (scripts/03_statistical_analysis.py); this gives the descriptive inputs.

with fct as (
    select * from {{ ref('fct_conversions') }}
),

by_group as (
    select
        test_group,
        count(*)           as n_users,
        sum(converted_int) as n_conversions,
        avg(converted_int) as conversion_rate,
        avg(total_ads)     as mean_total_ads
    from fct
    group by 1
),

pivoted as (
    select
        max(case when test_group = 'psa' then n_users end)          as n_psa,
        max(case when test_group = 'ad' then n_users end)            as n_ad,
        max(case when test_group = 'psa' then conversion_rate end)   as cr_psa,
        max(case when test_group = 'ad' then conversion_rate end)    as cr_ad,
        max(case when test_group = 'psa' then mean_total_ads end)    as mean_ads_psa,
        max(case when test_group = 'ad' then mean_total_ads end)     as mean_ads_ad
    from by_group
)

select
    n_psa,
    n_ad,
    n_psa + n_ad                                           as n_total,
    round(n_psa::float / (n_psa + n_ad), 4)                as pct_psa_holdout,
    cr_psa,
    cr_ad,
    round(cr_ad - cr_psa, 5)                               as absolute_lift,
    round((cr_ad - cr_psa) / nullif(cr_psa, 0) * 100, 3)   as relative_lift_pct,
    mean_ads_psa,
    mean_ads_ad
from pivoted
