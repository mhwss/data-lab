# Data Lab

Учебный проект по построению ETL-пайплайна для загрузки и обработки данных с использованием Python, ClickHouse, Airflow и Docker.
В качестве источника данных используется API Центрального банка РФ. Пайплайн получает историю курсов валют, преобразует и проверяет данные, после чего загружает их в ClickHouse.

## Стек

- Python 3.12
- pandas
- requests
- ClickHouse
- Apache Airflow
- Docker / Docker Compose

## Запуск

Собрать и запустить контейнеры:
```bash
docker compose up -d --build
```

Повторная сборка с `--build` требуется после изменений Dockerfile или зависимостей. Для обычного повторного запуска:
```bash
docker compose up -d
```

После запуска доступны:
- ClickHouse HTTP API — `localhost:8123`
- Airflow UI — `localhost:8080`

Пайплайн последовательно выполняет:

1. проверку входного диапазона дат
2. получение и преобразование данных
3. проверку DataFrame
4. очистку staging
5. загрузку staging
6. проверку staging
7. удаление периода из raw
8. перенос staging → raw
9. формирование результата