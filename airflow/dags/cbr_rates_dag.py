"""
DAG для загрузки истории курсов валют ЦБ РФ в clickhouse.
"""

from datetime import date, timedelta

from airflow.sdk import dag, task

from src.pipelines.cbr_pipeline import run_cbr_rates_pipeline


@dag(
    dag_id='cbr_rates',
    schedule=None,
    catchup=False,
    tags=['cbr'],
)
def cbr_rates_dag():

    @task
    def run_pipeline():
        end_date = date.today()
        start_date = end_date - timedelta(weeks=1)

        result = run_cbr_rates_pipeline(
            start_date=start_date,
            end_date=end_date,
        )

        if result['status'] != 'success':
            raise RuntimeError(
                f'CBR pipeline failed: {result ['error']}'
            )

        return result 

    run_pipeline()


cbr_rates_dag()