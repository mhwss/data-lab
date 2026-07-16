"""
Pipeline для получения истории курсов валют ЦБ РФ.

Модуль отвечает за:
- генерацию диапазона дат;
- запуск extract-функций по каждой дате;
- объединение дневных DataFrame;
- добавление технических полей RAW-слоя.
"""

from datetime import date
import time

import pandas as pd

from src.extract.cbr_api import get_cbr_rates_by_date
from src.load.clickhouse_load import(
    delete_currency_rates_by_source_date,
    load_currency_rates_to_clickhouse
)
from src.transform.cbr_transform import filter_target_currencies


def get_date_range(
    start_date: date,
    end_date: date
) -> list[date]:
    """
    Создать список дат между start_date и end_date включительно.
    """

    date_range = pd.date_range(
        start=start_date,
        end=end_date,
        freq='D'
    )

    request_dates = [
        current_date.date()
        for current_date in date_range
    ]

    return request_dates


def add_raw_metadata(
    currency_rates_df: pd.DataFrame,
    source_date: date
) -> pd.DataFrame:
    """
    Добавить технические поля RAW-слоя.
    """

    currency_rates_with_metadata_df = currency_rates_df.copy()

    currency_rates_with_metadata_df['source_date'] = pd.to_datetime(
        source_date
    )

    currency_rates_with_metadata_df['load_dttm'] = pd.Timestamp.now()

    column_order = [
        'load_dttm',
        'source_date',
        'rate_date',
        'currency_code',
        'currency_name',
        'nominal',
        'rate'
    ]

    currency_rates_with_metadata_df = (
        currency_rates_with_metadata_df[column_order]
    )

    return currency_rates_with_metadata_df


def get_cbr_rates_history(
    start_date: date,
    end_date: date
) -> pd.DataFrame:
    """
    Получить историю курсов валют ЦБ за период.
    """

    request_dates = get_date_range(
        start_date,
        end_date
    )

    currency_rates_frames = []

    for request_date in request_dates:
        currency_rates_day_df = get_cbr_rates_by_date(
            request_date
        )
        
        currency_rates_day_df = filter_target_currencies(
            currency_rates_day_df
        )

        currency_rates_day_with_metadata_df = add_raw_metadata(
            currency_rates_day_df,
            request_date
        )

        currency_rates_frames.append(
            currency_rates_day_with_metadata_df
        )

        time.sleep(0.2)

    currency_rates_history_df = pd.concat(
        currency_rates_frames,
        ignore_index=True
    )

    return currency_rates_history_df

def run_cbr_rates_pipeline(
   start_date: date,
   end_date: date
) -> dict:
   """
   Запустить полный pipeline загрузки курсов валют ЦБ за период.
   Шаги:
       1. Получить данные за период.
       2. Удалить старые данные за этот период из RAW-таблицы.
       3. Загрузить новые данные в ClickHouse.
   Returns
   -------
   dict
       Итог выполнения pipeline.
   """
   currency_rates_history_df = get_cbr_rates_history(
       start_date,
       end_date
   )
   delete_result = delete_currency_rates_by_source_date(
       start_date,
       end_date
   )
   load_result = load_currency_rates_to_clickhouse(
       currency_rates_history_df
   )
   pipeline_result = {
       'pipeline_name': 'cbr_rates_pipeline',
       'start_date': start_date,
       'end_date': end_date,
       'rows_loaded': load_result['rows_loaded'],
       'status': load_result['status'],
       'delete_result': delete_result,
       'load_result': load_result
   }
   return pipeline_result