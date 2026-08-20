## Структура проекта

data-lab/
|
|-- airflow/
|   |-- dags/
|       |-- cbr_rates_dag.py        # DAG запуска ETL пайплайна ЦБ РФ 
|
|-- sql/
|   |-- ddl/
|       |-- 01_schema.sql           # создание базы и таблиц
|
|-- src/
|   |-- common/
|   |   |-- ch_client.py            # подключение и запросы ClickHouse
|   |   |-- run_sql_file.py         # выполнение SQL-файлов
|   |
|   |-- config/
|   |   |-- logging_config.py       # настройка логирования
|   |   |-- settings.py             # настройки pipeline
|   |
|   |-- extract/
|   |   |-- cbr_api.py              # запрос и парсинг API ЦБ РФ
|   |
|   |-- transform/
|   |    |-- cbr_transform.py        # фильтрация валют
|   |
|   |-- quality/
|   |   |-- cbr_checks.py           # проверка DataFrame
|   |   |-- staging_quality.py      # проверка staging
|   |
|   |-- load/
|   |   |-- clickhouse_load.py      # загрузка staging и перенос в RAW
|   |
|   |-- pipelines/
|   |   |-- cbr_pipeline.py         # управление полным pipeline
|
|-- .env                            # параметры подключения, не хранится в Git
|-- .env.example                    # пример переменных окружения
|-- .gitignore                      # исключения Git
|-- docker-compose.yml              # запуск ClickHouse, Airflow
|-- Dockerfile.airflow              # образ Airflow с зависимостями проекта
|-- pyproject.toml                  # конфигурация Python-проекта
|-- README.md                       # описание проекта
|-- project_map.md                  # карта структуры проекта
