import datetime
from pathlib import Path
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from airflow.operators.s3_to_redshift_operator import S3ToRedshiftTransfer
from airflow.operators.check_operator import CheckOperator, ValueCheckOperator


# DAG default argument dictionary
default_args = {
    'owner': 'vineeths',
    'start_date': datetime.datetime(2020, 2, 1),
    'depends_on_past': False,
    'catchup': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': datetime.timedelta(minutes=5),
    'aws_conn_id': 'aws',
    'postgres_conn_id': 'redshift',
    'redshift_conn_id': 'redshift',
    'params': {
        's3_bucket': 'udacity-twitter-stream',
        's3_region': 'us-west-2',
        's3_json_path': None,
        'redshift_schema': 'public',
        'aws_iam_role': Variable.get("aws_iam_role")
    }
}

# Define DAG with template SQL path
with DAG(dag_id='capstone_dag',
         description='ETL data from S3 into AWS Redshift',
         default_args=default_args,
         schedule_interval='@daily',
         template_searchpath=str(Path(__file__).parent.parent.joinpath('sql'))) as dag:

    # Dummy start task
    start = DummyOperator(task_id='start_execution')

    # Create AWS Redshift cluster
    create_cluster = BashOperator(
        task_id='create_redshift_cluster',
        bash_command='python aws_cluster_create.py'
    )

    # Upload static datasets to S3 bucket
    upload_data_s3 = BashOperator(
        task_id='upload_data_to_s3',
        bash_command='python upload_to_s3.py'
    )

    # Stream tweet data to AWS Kineses
    stream_tweet = BashOperator(
        task_id='stream_data_to_kinesis',
        bash_command='python stream_tweets.py'
    )

    # Stream historical tweet data to AWS Kineses
    stream_historical_tweet = BashOperator(
        task_id='stream_batch_data_to_kinesis',
        bash_command='python search_tweets.py'
    )

    # Create the tables in AWS Redshift cluster
    create_tables = PostgresOperator(
        task_id='create_tables',
        sql='create_tables.sql'
    )

    # Stage tweets data in Redshift
    stage_tweets = S3ToRedshiftTransfer(
        task_id='stage_tweets',
        schema='{{ params.redshift_schema }}',
        table='staging_tweets',
        s3_bucket='{{ params.s3_bucket }}',
        s3_key='twitter_feed',
        copy_options=['COMPUPDATE OFF', 'STATUPDATE OFF', 'TRUNCATECOLUMNS']
    )

    # Stage happiness data in Redshift
    stage_happiness = S3ToRedshiftTransfer(
        task_id='stage_happiness',
        schema='{{ params.redshift_schema }}',
        table='staging_happiness',
        s3_bucket='{{ params.s3_bucket }}',
        s3_key='happiness',
        copy_options=['COMPUPDATE OFF', 'STATUPDATE OFF', 'TRUNCATECOLUMNS']
    )

    # Stage temperature data in Redshift
    stage_temperature = S3ToRedshiftTransfer(
        task_id='stage_temperature',
        schema='{{ params.redshift_schema }}',
        table='staging_temperature',
        s3_bucket='{{ params.s3_bucket }}',
        s3_key='temperature',
        copy_options=['COMPUPDATE OFF', 'STATUPDATE OFF', 'TRUNCATECOLUMNS']
    )

    # Runs a basic data quality check to ensure data is inserted
    check_tweets = CheckOperator(
        task_id='quality_check_staging_tweets_table',
        sql='SELECT COUNT(*) FROM public.staging_tweets',
        conn_id='{{ redshift_conn_id }}'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_happiness = ValueCheckOperator(
        task_id='quality_check_staging_happiness_table',
        sql='SELECT COUNT(*) FROM public.staging_happiness',
        pass_value=154,
        conn_id='{{ redshift_conn_id }}'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_temperature = ValueCheckOperator(
        task_id='quality_check_staging_temperature_table',
        sql='SELECT COUNT(*) FROM public.staging_temperature',
        pass_value=8599212,
        conn_id='{{ redshift_conn_id }}'
    )

    # Load user table from staging tables
    load_users_table = PostgresOperator(
        task_id='load_users_table',
        sql='users_insert.sql'
    )

    # Load sources table from staging tables
    load_sources_table = PostgresOperator(
        task_id='load_sources_table',
        sql='sources_insert.sql'
    )

    # Load happiness table from staging tables
    load_happiness_table = PostgresOperator(
        task_id='load_happiness_table',
        sql='happiness_insert.sql'
    )

    # Load temperature table from staging tables
    load_temperature_table = PostgresOperator(
        task_id='load_temperature_table',
        sql='temperature_insert.sql'
    )

    # Load time table from staging tables
    load_time_table = PostgresOperator(
        task_id='load_time_table',
        sql='time_insert.sql'
    )

    # Load tweets table from staging tables
    load_tweets_table = PostgresOperator(
        task_id='load_tweets_fact_table',
        sql='tweets_insert.sql'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_users_dim = CheckOperator(
        task_id='quality_check_users_table',
        sql='SELECT COUNT(*) FROM public.users',
        conn_id='{{ redshift_conn_id }}'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_sources_dim = CheckOperator(
        task_id='quality_check_sources_table',
        sql='SELECT COUNT(*) FROM public.sources',
        conn_id='{{ redshift_conn_id }}'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_happiness_dim = CheckOperator(
        task_id='quality_check_dim_happiness_table',
        sql='SELECT COUNT(*) FROM public.happiness',
        conn_id='{{ redshift_conn_id }}'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_temperature_dim = CheckOperator(
        task_id='quality_check_dim_temperature_table',
        sql='SELECT COUNT(*) FROM public.temperature',
        conn_id='{{ redshift_conn_id }}'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_time = CheckOperator(
        task_id='quality_check_time_table',
        sql='SELECT COUNT(*) FROM public.time',
        conn_id='{{ redshift_conn_id }}'
    )

    # Runs a basic data quality check to ensure data is inserted
    check_tweets_fact = CheckOperator(
        task_id='quality_check_fact_tweets_table',
        sql='SELECT COUNT(*) FROM public.tweets',
        conn_id='{{ redshift_conn_id }}'
    )

    # Destroy AWS Redshift cluster
    destroy_cluster = BashOperator(
        task_id='destroy_redshift_cluster',
        bash_command='python aws_cluster_destroy.py'
    )

    # Dummy end task
    end = DummyOperator(task_id='stop_execution')

    # Setup task dependencies
    """
    # Stream real time tweets (Uncomment this block and comment next block)
    start >> upload_data_s3 >> stream_tweet >> create_tables >> [stage_tweets,
                                                                 stage_happiness,
                                                                 stage_temperature]
    """

    # Stream historical tweets
    start >> create_cluster >> upload_data_s3 >> stream_historical_tweet >> create_tables >> [stage_tweets,
                                                                                              stage_happiness,
                                                                                              stage_temperature]

    [stage_tweets >> check_tweets,
     stage_happiness >> check_happiness,
     stage_temperature >> check_temperature] >> load_tweets_table >> check_tweets_fact >> [load_users_table,
                                                                                           load_sources_table,
                                                                                           load_happiness_table,
                                                                                           load_temperature_table,
                                                                                           load_time_table]

    [load_users_table >> check_users_dim,
     load_sources_table >> check_sources_dim,
     load_happiness_table >> check_happiness_dim,
     load_temperature_table >> check_temperature_dim,
     load_time_table >> check_time] >> destroy_cluster >> end
