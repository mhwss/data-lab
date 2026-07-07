"""
Проверки качества данных для курсов валют ЦБ.

Модуль отвечает за валидацию DataFrame.
"""

import pandas as pd


REQUIRED_CBR_COLUMNS = [
    'load_dttm',
    'source_date',
    'rate_date',
    'currency_code',
    'currency_name',
    'nominal',
    'rate'
]


def validate_cbr_rates_df(
    currency_rates_df: pd.DataFrame
) -> dict:
    """
    Проверить качество DataFrame с курсами валют.

    Returns
    -------
    dict
        Результат проверки.
    """

    errors = []

    if currency_rates_df.empty:
        errors.append('DataFrame is empty')

    missing_columns = [
        column_name
        for column_name in REQUIRED_CBR_COLUMNS
        if column_name not in currency_rates_df.columns
    ]

    if missing_columns:
        errors.append(f'Missing columns: {missing_columns}')

    if not missing_columns:
        key_columns = [
            'source_date',
            'currency_code'
        ]

        null_counts = (
            currency_rates_df[REQUIRED_CBR_COLUMNS]
            .isna()
            .sum()
        )

        columns_with_nulls = (
            null_counts[null_counts > 0]
            .to_dict()
        )

        if columns_with_nulls:
            errors.append(f'Null values found: {columns_with_nulls}')

        duplicate_rows_count = (
            currency_rates_df
            .duplicated(subset=key_columns)
            .sum()
        )

        if duplicate_rows_count > 0:
            errors.append(
                f'Duplicates found by {key_columns}: {duplicate_rows_count}'
            )

        invalid_rate_count = (
            currency_rates_df['rate'] <= 0
        ).sum()

        if invalid_rate_count > 0:
            errors.append(f'Invalid rate values: {invalid_rate_count}')

        invalid_nominal_count = (
            currency_rates_df['nominal'] <= 0
        ).sum()

        if invalid_nominal_count > 0:
            errors.append(f'Invalid nominal values: {invalid_nominal_count}')

    validation_result = {
        'status': 'success' if not errors else 'failed',
        'row_count': len(currency_rates_df),
        'errors': errors
    }

    return validation_result