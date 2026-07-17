from pathlib import Path
import os

print('Текущая директория:', os.getcwd())
print('Файл находится:', Path(__file__).resolve())

from ch_client import ch_execute, ch_select


def run_sql_file(path: str) -> None:
    sql_path = Path(path)

    print("SQL path:", sql_path.resolve())
    print("File exists:", sql_path.exists())

    sql_text = sql_path.read_text(encoding="utf-8")

    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]

    print("Statements count:", len(statements))

    for i, statement in enumerate(statements, start=1):
        print(f"\nExecuting statement {i}:")
        print(statement[:200])

        ch_execute(statement)

        print("Done")


if __name__ == "__main__":
    run_sql_file("sql/ddl/01_schema.sql")

    print(ch_select("SHOW DATABASES"))