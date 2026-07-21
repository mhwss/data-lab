import os

import clickhouse_connect
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def get_client():
    """
    Создаёт подключение к ClickHouse.
    """
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ["CLICKHOUSE_PORT"]),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
    )

def ch_execute(sql: str) -> None:
    """
    Выполняет SQL-команды без возврата таблицы:
    CREATE, DROP, TRUNCATE, INSERT SELECT.
    """
    client = get_client()
    client.command(sql)

def ch_select(sql: str) -> pd.DataFrame:
    """
    Выполняет SELECT и возвращает результат как pandas DataFrame.
    """
    client = get_client()
    return client.query_df(sql)

def ch_insert_dataframe(
        dataframe: pd.DataFrame,
        table_name: str,
) -> None:
    """
    Загружает DataFrame в таблицу ClickHouse
    """
    client = get_client()
    client.insert_df(
        table=table_name,
        df=dataframe,
    )

def ch_scalar(sql: str):
    """
    Выполняет SQL-запрос и возвращает одно значение.
    Для запросов:
    - SELECT count(*)
    - SELECT min(*)
    - SELECT max(*)
    """
    client = get_client()

    result = client.query(sql)

    if not result.result_rows:
        return None
    
    return result.result_rows[0][0]

if __name__ == "__main__":
    result_df = ch_select("SELECT 1 AS ping")
    print(result_df)