"""
Pipeline для получения истории курсов валют ЦБ РФ.

Модуль отвечает за:
- генерацию диапазона дат;
- запуск extract-функций по каждой дате;
- объединение дневных DataFrame;
- добавление технических полей RAW-слоя.
"""

from datetime import date, timezone
import time
import logging

import pandas as pd

from src.extract.cbr_api import get_cbr_rates_by_date
from src.load.clickhouse_load import(
    delete_currency_rates_by_source_date,
    load_currency_rates_to_clickhouse
)
from src.transform.cbr_transform import filter_target_currencies
from src.quality.cbr_checks import validate_cbr_rates_df
from src.config.settings import CBR_REQUEST_DELAY_SECONDS

from src.config.logging_config import configure_logging

configure_logging()

logger = logging.getLogger(__name__)



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

    currency_rates_with_metadata_df['load_dttm'] = pd.Timestamp.now(timezone.utc)

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

        time.sleep(CBR_REQUEST_DELAY_SECONDS)

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
       2. Оставить только USD, EUR, JPY, CNY.
       3. Добавить технические поля RAW-слоя.
       4. Проверить качество даннных.
       5. При ошибке качества остановить pipeline.
       6. Удалить старые данные за этот период из RAW-таблицы.
       7. Загрузить новые данные в ClickHouse.
   Returns
   -------
   dict
       Итог выполнения pipeline.
   """
   current_stage = 'start'

   logger.info(
      'Запуск pipeline ЦБ за период %s - %s',
      start_date,
      end_date
    )
   try:
      current_stage = 'extract'

      currency_rates_history_df = get_cbr_rates_history(
       start_date,
       end_date
       )
      
      logger.info(
          'Получено строк после extract и transform: %s',
          len(currency_rates_history_df)
          )
      
      current_stage = 'quality'

      validation_result = validate_cbr_rates_df(
          currency_rates_history_df
          )
      
      if validation_result['status'] != 'success':
        logger.error(
            'Проверка качества не пройдена: %s',
            validation_result['errors']
            )
        
        return {
           'pipeline_name': 'cbr_rates_pipeline',
           'start_date': start_date,
           'end_date': end_date,
           'rows_loaded': 0,
           'status': 'failed',
           'validation_result': validation_result,
           'delete_result': None,
           'load_result': None
           }
        
      logger.info(
         'Проверка качества пройдена. Количество строк: %s',
         validation_result['row_count']
         )
      
      current_stage = 'delete'
      
      delete_result = delete_currency_rates_by_source_date(
         start_date=start_date,
         end_date=end_date
         )
      
      logger.info(
         'Удаление старых данных завершено со статусом: %s',
         delete_result['status']
         )
      
      current_stage = 'load'
      
      load_result = load_currency_rates_to_clickhouse(
         currency_rates_history_df
         )
      
      logger.info(
         'Загрузка завершена. Загружено строк: %s',
         load_result['rows_loaded']
         )
      
      current_stage = 'completed'
      
      pipeline_result = {
         'pipeline_name': 'cbr_rates_pipeline',
         'start_date': start_date,
         'end_date': end_date,
         'rows_loaded': load_result['rows_loaded'],
         'status': load_result['status'],
         'validation_result': validation_result,
         'delete_result': delete_result,
         'load_result': load_result
         }
      
      logger.info('Pipeline ЦБ успешно завершен')
      
      return pipeline_result
   
   except Exception as error:
      logger.exception(
         'Pipeline ЦБ завершился с ошибкой на этапе %s: %s',
         current_stage,
         error
      )

      return{
         'pipeline_name': 'cbr_rates_pipeline',
         'start_date': start_date,
         'end_date': end_date,
         'rows_loaded': 0,
         'status': 'failed',
         'stage': current_stage,
         'error': str(error)
      }