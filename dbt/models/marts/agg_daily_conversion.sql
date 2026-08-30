-- Conversion rate by day of week x test group. Powers the stability
-- ("is the lift positive every day") chart in the BI dashboard.

with fct as (
    select * from {{ ref('fct_conversions') }}
)

select
    most_ads_day,
    test_group,
    count(*)           as users,
    sum(converted_int) as conversions,
    avg(converted_int) as conversion_rate
from fct
group by 1, 2
order by 1, 2
