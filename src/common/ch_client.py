import os
import clickhouse_connect
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

def ch_select(sql: str):
    """
    Выполняет SELECT и возвращает результат как pandas DataFrame.
    """
    client = get_client()
    return client.query_df(sql)

if __name__ == "__main__":
    print(ch_execute("SELECT 1"))

    df = ch_select("""
        SELECT
            name
        FROM system.tables
        LIMIT 10
    """)

    print(df)