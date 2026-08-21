"""
Pipeline для получения истории курсов валют ЦБ РФ.

Модуль отвечает за:
- генерацию диапазона дат;
- запуск extract-функций по каждой дате;
- объединение дневных DataFrame;
- добавление технических полей RAW-слоя.
"""

import logging
import time
from datetime import date, timedelta

import pandas as pd

from src.extract.cbr_api import get_cbr_rates_by_date
from src.load.clickhouse_load import (
    delete_currency_rates_by_source_date,
    insert_from_table,
    load_currency_rates_to_staging,
    truncate_table,
)
from src.transform.cbr_transform import filter_target_currencies
from src.quality.cbr_checks import validate_cbr_rates_df
from src.quality.staging_quality import validate_staging
from src.config.settings import (
    CBR_REQUEST_DELAY_SECONDS,
    CBR_RATES_STAGING_TABLE_NAME,
    CBR_RATES_TABLE_NAME,
)

from src.config.logging_config import configure_logging

configure_logging()

logger = logging.getLogger(__name__)



def get_date_range(
    start_date: date,
    end_date: date,
) -> list[date]:
    """
    Создать список дат между start_date и end_date включительно.
    """

    date_range = pd.date_range(
        start=start_date,
        end=end_date,
        freq='D',
    )

    request_dates = [
        current_date.date()
        for current_date in date_range
    ]

    return request_dates


def add_raw_metadata(
    currency_rates_df: pd.DataFrame,
    source_date: date,
) -> pd.DataFrame:
    """
    Добавить технические поля RAW-слоя.
    """

    currency_rates_with_metadata_df = currency_rates_df.copy()

    currency_rates_with_metadata_df['source_date'] = pd.to_datetime(
        source_date,
    )

    currency_rates_with_metadata_df['load_dttm'] = (
        pd.Timestamp.now(tz='UTC').tz_localize(None)
    )

    column_order = [
        'load_dttm',
        'source_date',
        'rate_date',
        'currency_code',
        'currency_name',
        'nominal',
        'rate',
    ]

    currency_rates_with_metadata_df = (
        currency_rates_with_metadata_df[column_order]
    )

    return currency_rates_with_metadata_df


def get_cbr_rates_history(
    start_date: date,
    end_date: date,
) -> pd.DataFrame:
    """
    Получить историю курсов валют ЦБ за период.
    """

    request_dates = get_date_range(
        start_date,
        end_date,
    )

    currency_rates_frames = []

    for request_date in request_dates:
        currency_rates_day_df = get_cbr_rates_by_date(
            request_date,
        )
        
        currency_rates_day_df = filter_target_currencies(
            currency_rates_day_df,
        )

        currency_rates_day_with_metadata_df = add_raw_metadata(
            currency_rates_day_df,
            request_date,
        )

        currency_rates_frames.append(
            currency_rates_day_with_metadata_df,
        )

        time.sleep(CBR_REQUEST_DELAY_SECONDS)

    currency_rates_history_df = pd.concat(
        currency_rates_frames,
        ignore_index=True,
    )

    return currency_rates_history_df

def run_cbr_rates_pipeline(
    start_date: date,
    end_date: date,
) -> dict:
    """
    Запустить полный pipeline загрузки курсов валют ЦБ за период.
    Шаги:
        1. Получить данные за период.
        2. Оставить только USD, EUR, JPY, CNY.
        3. Добавить технические поля RAW-слоя.
        4. Проверить качество даннных.
        5. Очистить staging таблицу.
        6. Загрузить данные в staging.
        7. Проверить staging.
        8. При ошибке качества остановить pipeline.
        9. Удалить старые данные за этот период из RAW-таблицы.
        10. Перенести данные из staging в RAW.
    Returns
    -------
    dict
        Итог выполнения pipeline.
    """
    current_stage = 'start'
    rows_extracted = 0

    validation_result = None
    staging_load_result = None
    delete_result = None
    load_result = None

    logger.info(
        'Запуск pipeline ЦБ за период %s - %s',
        start_date,
        end_date,
        )
    
    try:
        current_stage = 'validate_input'

        if start_date > end_date:
            raise ValueError(
                'Начальная дата не может быть больше конечной даты',
            )
        
        current_stage = 'extract_transform'

        currency_rates_history_df = get_cbr_rates_history(
            start_date,
            end_date,
        )
        
        rows_extracted = len(currency_rates_history_df)
        
        logger.info(
            'Получено строк после извлечения и преобразования: %s',
            rows_extracted,
        )
        
        if currency_rates_history_df.empty:
            raise ValueError(
                'Получен пустой DataFrame',
            )
        
        current_stage = 'validate_dataframe'

        validation_result = validate_cbr_rates_df(
            currency_rates_history_df,
        )
        
        if validation_result['status'] != 'success':
            logger.error(
                'Проверка качества не пройдена: %s',
                validation_result['errors'],
                )
            
            return {
                'pipeline_name': 'cbr_rates_pipeline',
                'start_date': start_date,
                'end_date': end_date,
                'rows_extracted': rows_extracted,
                'rows_loaded': 0,
                'status': 'failed',
                'stage': current_stage,
                'validation_result': validation_result,
                'staging_load_result': None,
                'delete_result': None,
                'load_result': None,
                'error': 'Проверка качества DataFrame не пройдена',
            }
            
        logger.info(
            'Проверка качества пройдена. Количество строк: %s',
            validation_result['row_count'],
            )
        
        current_stage = 'truncate_staging'
        
        truncate_table(
            table_name=CBR_RATES_STAGING_TABLE_NAME,
        )
        
        logger.info(
            'Staging таблица очищена: %s',
            CBR_RATES_STAGING_TABLE_NAME,
            )
        
        current_stage = 'load_staging'
        
        staging_load_result = load_currency_rates_to_staging(
            currency_rates_df=currency_rates_history_df,
            )
        
        logger.info(
            'Загрузка в staging завершена. Загружено строк: %s',
            staging_load_result['rows_loaded'],
            )
        
        current_stage = 'validate_staging'

        validate_staging(
            dataframe=currency_rates_history_df,
            table_name=CBR_RATES_STAGING_TABLE_NAME,
        )

        logger.info('Проверка staging пройдена')

        current_stage = 'delete_raw'

        delete_result = delete_currency_rates_by_source_date(
            start_date=start_date,
            end_date=end_date,
            table_name=CBR_RATES_TABLE_NAME,
        )

        logger.info(
            'Удаление старых данных из raw таблицы завершено со статусом: %s',
            delete_result['status'],
        )
        
        current_stage = 'load_raw'

        load_result = insert_from_table(
            staging_table_name=CBR_RATES_STAGING_TABLE_NAME,
            raw_table_name=CBR_RATES_TABLE_NAME,
        )

        logger.info(
            'Публикация staging в raw завершена. Загружено строк %s',
            load_result['rows_loaded'],
        )
        
        current_stage = 'completed'
        
        pipeline_result = {
            'pipeline_name': 'cbr_rates_pipeline',
            'start_date': start_date,
            'end_date': end_date,
            'rows_extracted': rows_extracted,
            'rows_loaded': load_result['rows_loaded'],
            'status': 'success',
            'stage': current_stage,
            'validation_result': validation_result,
            'staging_load_result': staging_load_result,
            'delete_result': delete_result,
            'load_result': load_result,
            'error': None,
            }
        
        logger.info(
            'Pipeline ЦБ успешно завершен. '
            'Загружено строк в raw-таблицу: %s',
            pipeline_result['rows_loaded'],
            )
        
        return pipeline_result
    
    except Exception as error:
        logger.exception(
            'Pipeline ЦБ завершился с ошибкой на этапе %s: %s',
            current_stage,
            error,
        )

        return{
            'pipeline_name': 'cbr_rates_pipeline',
            'start_date': start_date,
            'end_date': end_date,
            'rows_extracted': rows_extracted,
            'rows_loaded': 0,
            'status': 'failed',
            'stage': current_stage,
            'validation_result': validation_result,
            'staging_load_result': staging_load_result,
            'delete_result': delete_result,
            'load_result': load_result,
            'error': str(error),
        }


if __name__ == '__main__':
    end_date = date.today()
    start_date = end_date - timedelta(weeks=1)

    result = run_cbr_rates_pipeline(
        start_date=start_date,
        end_date=end_date,
    )

    print(result)