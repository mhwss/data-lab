"""
Функции загрузки данных в ClickHouse.

Модуль отвечает за запись готовых DataFrame в таблицы ClickHouse.
"""
from datetime import date

import pandas as pd

from src.common.ch_client import get_client




RAW_CBR_RATES_TABLE = 'data_lab.raw_cbr_rates'

def delete_currency_rates_by_source_date(
    start_date: date,
    end_date: date
) -> dict:
    """
    Удалить данные из RAW-таблицы за период source_date.

    Используется перед повторной загрузкой периода,
    чтобы избежать дублей при перезапуске pipeline.
    """

    clickhouse_client = get_client()

    delete_sql = f"""
        ALTER TABLE {RAW_CBR_RATES_TABLE}
        DELETE
        WHERE source_date BETWEEN '{start_date}' AND '{end_date}'
    """

    clickhouse_client.command(delete_sql)

    delete_result = {
        'table_name': RAW_CBR_RATES_TABLE,
        'start_date': start_date,
        'end_date': end_date,
        'status': 'success'
    }

    return delete_result

def load_currency_rates_to_clickhouse(
    currency_rates_df: pd.DataFrame
) -> dict:
    """
    Загрузить курсы валют в RAW-таблицу ClickHouse.
    """

    clickhouse_client = get_client()

    rows_loaded = len(currency_rates_df)

    clickhouse_client.insert_df(
        table=RAW_CBR_RATES_TABLE,
        df=currency_rates_df
    )

    load_result = {
        'table_name': RAW_CBR_RATES_TABLE,
        'rows_loaded': rows_loaded,
        'status': 'success'
    }

    return load_result