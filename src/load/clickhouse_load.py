"""
Функции загрузки данных в ClickHouse.

Модуль отвечает за запись готовых DataFrame в таблицы ClickHouse.
"""
import pandas as pd
from datetime import date

from src.common.ch_client import ch_execute, ch_scalar, ch_insert_dataframe
from src.config.settings import (
    CBR_RATES_STAGING_TABLE_NAME,
    CBR_RATES_TABLE_NAME, 
)


def truncate_table(table_name: str) -> None:
    """
    Полная очистка указанной таблицы ClickHouse.
    """
    sql = f"""
        TRUNCATE TABLE {table_name}
    """
    ch_execute(sql)


def delete_currency_rates_by_source_date(
    start_date: date,
    end_date: date,
    table_name: str = CBR_RATES_TABLE_NAME,
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
        SETTINGS mutations_sync = 1
    """
    ch_execute(delete_sql)

    return {
        'table_name': table_name,
        'start_date': start_date,
        'end_date': end_date,
        'status': 'success',
    }


def load_currency_rates_to_staging(
    currency_rates_df: pd.DataFrame,
) -> dict:
    """
    Загрузить DataFrame с курсами валют в staging таблицу
    """
    if currency_rates_df.empty:
        raise ValueError('Пустой DataFrame')
    
    rows_loaded = len(currency_rates_df)

    ch_insert_dataframe(
        dataframe=currency_rates_df,
        table_name=CBR_RATES_STAGING_TABLE_NAME,
    )

    return {
        'table_name': CBR_RATES_STAGING_TABLE_NAME,
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

def insert_from_table(
    staging_table_name: str,
    raw_table_name: str,
) -> dict:
    """
    Перенести строки из staging в RAW-таблицу.
    """

    rows_loaded = get_table_row_count(
        table_name=staging_table_name,
    )

    sql = f"""
        INSERT INTO {raw_table_name}
        SELECT *
        FROM {staging_table_name}
    """

    ch_execute(sql)

    return {
        'status': 'success',
        'rows_loaded': rows_loaded,
        'staging_table_name': staging_table_name,
        'raw_table_name': raw_table_name,
    }