

src/common
    ch_client.py
        get_client()
        ch_execute()
            get_client()
        ch_select()
            get_client()
        ch_insert_dataframe()
            get_client()
        ch_scalar()
            get_client()

    run_sql_file.py
        run_sql_file()
            ch_execute()
            ch_select()

src/config
    settings.py
        CBR_TARGET_CURRENCY_CODES
        CBR_REQUEST_DELAY_SECONDS
        CBR_RATES_TABLE_NAME
        CBR_RATES_STAGING_TABLE_NAME
        CBR_VERIFY_SSL

    logging_config.py
        configure_logging()

src/extract
    cbr_api.py
        fetch_cbr_xml() - "Получить курсы валют на указанную дату"

        parse_cbr_exchange_rates() - "Преобразовать XML ЦБ в pandas DataFrame"

        get_cbr_rates_by_date()
            fetch_cbr_xml()
            parse_cbr_exchange_rates()

src/quality
    cbr_checks.py
        REQUIRED_CBR_COLUMNS

        validate_cbr_rates_df() - "Проверить качество DataFrame с курсами валют."


src/transform
    cbr_transform.py
        src.config.settings CBR_TARGET_CURRENCY_CODES


src/load
    clickhouse_load.py
        truncate_table()

        delete_currency_rates_by_source_date()

        CBR_RATES_TABLE_NAME

        load_currency_rates_to_clickhouse()

        get_table_row_count()
            ch_scalar()




src/pipeline
    cbr_pipeline.py
        get_date_range()

        add_raw_metadata()

        get_cbr_rates_history()
            CBR_REQUEST_DELAY_SECONDS
            get_date_range()
            get_cbr_rates_by_date()
            filter_target_currencies()
            add_raw_metadata()

        run_cbr_rates_pipeline()



