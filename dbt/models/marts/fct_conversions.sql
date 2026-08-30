-- BI-ready fact table: one row per user with dimension keys + the binary
-- conversion measure, for slicing by group/day/hour/exposure in Tableau
-- or Looker Studio.

with users as (
    select * from {{ ref('dim_users') }}
)

select
    user_id,
    test_group,
    total_ads,
    most_ads_day,
    most_ads_hour,
    exposure_bucket,
    converted,
    case when converted then 1 else 0 end as converted_int
from users
