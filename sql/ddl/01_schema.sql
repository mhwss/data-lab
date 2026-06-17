CREATE DATABASE IF NOT EXISTS data_lab;

CREATE TABLE IF NOT EXISTS data_lab.raw_cbr_rates
(
    load_dttm DateTime,
    source_date Date,
    rate_date Date,
    currency_code String,
    currency_name String,
    nominal UInt32,
    rate Float64
)
ENGINE = MergeTree
ORDER BY (rate_date, currency_code, load_dttm);