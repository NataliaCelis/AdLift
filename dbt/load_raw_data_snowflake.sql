-- ============================================================================
-- One-time setup: load marketing_ab_clean.csv into Snowflake as the RAW
-- source table dbt's staging model reads from.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS AD_LIFT;
CREATE SCHEMA IF NOT EXISTS AD_LIFT.RAW;
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60;

CREATE OR REPLACE FILE FORMAT AD_LIFT.RAW.CSV_STANDARD
  TYPE = 'CSV'
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NULL');

CREATE OR REPLACE TABLE AD_LIFT.RAW.AD_EVENTS (
    user_id        NUMBER,
    test_group     VARCHAR,      -- 'ad' | 'psa'
    converted      BOOLEAN,
    total_ads      NUMBER,       -- ad-slot impressions seen
    most_ads_day   VARCHAR,
    most_ads_hour  NUMBER
);

-- Option A: Snowsight UI -> Data > Add Data > Load files into a Table
--   Target: AD_LIFT.RAW.AD_EVENTS, using the CSV_STANDARD file format.
--
-- Option B: SnowSQL / CLI
--   PUT file:///path/to/marketing_ab_clean.csv @AD_LIFT.RAW.%AD_EVENTS;
--   COPY INTO AD_LIFT.RAW.AD_EVENTS
--     FROM @AD_LIFT.RAW.%AD_EVENTS
--     FILE_FORMAT = (FORMAT_NAME = AD_LIFT.RAW.CSV_STANDARD)
--     ON_ERROR = 'CONTINUE';

-- Sanity check after load:
-- SELECT test_group, COUNT(*), AVG(converted::int) FROM AD_LIFT.RAW.AD_EVENTS GROUP BY 1;
