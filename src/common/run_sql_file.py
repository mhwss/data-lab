from pathlib import Path

from src.common.ch_client import ch_execute, ch_select

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_sql_file(
        path: str | Path,
) -> None:
    """
    Прочитать sql файл и последовательно выполнить его команды.
    """

    sql_path = Path(path)

    if not sql_path.is_absolute():
        sql_path = PROJECT_ROOT / sql_path
    
    if not sql_path.exists():
        raise FileNotFoundError(
            f'SQL-файл не найден: {sql_path.resolve()}'
        )
    
    sql_text = sql_path.read_text(encoding='utf-8')

    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]

    print(f'SQL-файл: {sql_path.resolve()}')
    print(f'Количество команд: {len(statements)}')

    print('Statements count:', len(statements))

    for statment_number, statement in enumerate(
        statements, 
        start=1,
    ):
        print(f'\nВыполняется команда {statment_number}:')
        print(statement[:200])

        ch_execute(statement)

        print('Выполнено')


if __name__ == '__main__':
    run_sql_file('sql/ddl/01_schema.sql')

    print(ch_select('SHOW DATABASES'))