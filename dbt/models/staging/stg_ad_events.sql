-- Staging: standardize types/casing. This dataset arrives clean (no
-- duplicate users, no nulls, no invalid categories - verified in
-- scripts/02_data_cleaning.py), so this model is mostly a typed passthrough
-- plus a defensive dedupe in case of a future re-load.

with source as (
    select * from {{ source('raw', 'ad_events') }}
),

standardized as (
    select
        user_id,
        lower(trim(test_group)) as test_group,
        converted,
        total_ads,
        initcap(trim(most_ads_day)) as most_ads_day,
        most_ads_hour
    from source
    where lower(trim(test_group)) in ('ad', 'psa')
),

deduped as (
    select
        *,
        row_number() over (partition by user_id order by user_id) as rn
    from standardized
)

select
    user_id,
    test_group,
    converted,
    total_ads,
    most_ads_day,
    most_ads_hour
from deduped
where rn = 1
