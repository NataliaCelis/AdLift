-- One row per user: arm assignment, exposure, and outcome.

with stg as (
    select * from {{ ref('stg_ad_events') }}
)

select
    user_id,
    test_group,
    converted,
    total_ads,
    most_ads_day,
    most_ads_hour,
    case
        when total_ads <= 4 then '1_low (<=4)'
        when total_ads <= 13 then '2_medium (5-13)'
        when total_ads <= 27 then '3_high (14-27)'
        else '4_very_high (28+)'
    end as exposure_bucket
from stg
