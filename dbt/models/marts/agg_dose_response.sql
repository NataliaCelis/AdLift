-- Conversion rate by ad-exposure bucket (ad group only) - the dose-response
-- guardrail that supports a causal story, not just correlation.

with fct as (
    select * from {{ ref('fct_conversions') }}
    where test_group = 'ad'
)

select
    exposure_bucket,
    count(*)             as users,
    avg(total_ads)        as mean_total_ads,
    sum(converted_int)    as conversions,
    avg(converted_int)    as conversion_rate
from fct
group by 1
order by 1
