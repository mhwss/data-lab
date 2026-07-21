"""
Функции загрузки данных в ClickHouse.

Модуль отвечает за запись готовых DataFrame в таблицы ClickHouse.
"""
from datetime import date

import pandas as pd

from src.common.ch_client import get_client, ch_execute, ch_scalar
from src.config.settings import CBR_RATES_TABLE_NAME


def truncate_table(table_name: str) -> None:
    """
    Полная очистка укзаанной таблицы ClickHouse.
    """
    sql = f"""
            TRUNCATE TABLE {table_name}
        """
    ch_execute(sql)


def delete_currency_rates_by_source_date(
    start_date: date,
    end_date: date,
    table_name: str = CBR_RATES_TABLE_NAME
) -> dict:
    """
    Удалить данные из RAW-таблицы за период source_date.

    Используется перед повторной загрузкой периода,
    чтобы избежать дублей при перезапуске pipeline.
    """
    delete_sql = f"""
        ALTER TABLE {table_name}
        DELETE
        WHERE source_date BETWEEN '{start_date}' AND '{end_date}'
    """
    ch_execute(delete_sql)

    return {
        'table_name': table_name,
        'start_date': start_date,
        'end_date': end_date,
        'status': 'success'
    }


def load_currency_rates_to_clickhouse(
    currency_rates_df: pd.DataFrame,
    table_name: str = CBR_RATES_TABLE_NAME,
) -> dict:
    """
    Загрузить курсы валют в RAW-таблицу ClickHouse.
    """
    if currency_rates_df.empty:
        raise ValueError("Пустой DataFrame")
    
    clickhouse_client = get_client()

    rows_loaded = len(currency_rates_df)

    clickhouse_client.insert_df(
        table=table_name,
        df=currency_rates_df,
    )

    return {
        'table_name': table_name,
        'rows_loaded': rows_loaded,
        'status': 'success',
    }

def get_table_row_count(
        table_name: str,
) -> int:
    """
    Возвращает количество строк в таблице Clickhouse.
    """

    row_count = ch_scalar(
        f"""
            SELECT count(*)
            FROM {table_name}
        """
    )

    return int(row_count)