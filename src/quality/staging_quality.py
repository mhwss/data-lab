import pandas as pd

from src.load.clickhouse_load import get_table_row_count

def validate_staging(
        dataframe: pd.DataFrame,
        table_name: str,
) -> None:
    """
    Проверяет, что количество строк в DataFrame совпадает с количеством строк в staging-таблице.
    """
    dataframe_row_count = len(dataframe)

    staging_row_count = get_table_row_count(
        table_name=table_name,
    )

    if dataframe_row_count != staging_row_count:
        raise ValueError(
            "Количество строк в DataFrame "
            "не совпадает с количеством строк в staging: "
            f"{dataframe_row_count} != {staging_row_count}"
        )