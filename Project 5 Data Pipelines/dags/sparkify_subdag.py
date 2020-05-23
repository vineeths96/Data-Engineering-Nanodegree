import datetime
from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators import LoadDimensionOperator
from helpers import SqlQueries


def load_dimensional_tables_dag(
        parent_dag_name,
        task_id,
        redshift_conn_id,
        aws_credentials_id,
        table,
        sql_query,
        *args, **kwargs):
    """
    Returns a DAG (SubDAG) that inserts data into a dimensional tables from staging tables in Redshift
    """
    
    dag = DAG(
        f"{parent_dag_name}.{task_id}",
        **kwargs
    )

    load_dimension_table = LoadDimensionOperator(
        task_id=f"load_{table}_dim_table",
        dag=dag,
        table=table,
        redshift_conn_id=redshift_conn_id,
        sql_query=sql_query
    )

    load_dimension_table

    return dag