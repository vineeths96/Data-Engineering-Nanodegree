from airflow.hooks.postgres_hook import PostgresHook
from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


class CreateTablesOperator(BaseOperator):
    """
    Airflow Operator to create tables in the AWS Redshift cluster
    """
    
    ui_color = '#358140'
    sql_file='/home/workspace/airflow/create_tables.sql'

    @apply_defaults
    def __init__(self,
                 redshift_conn_id="",
                 *args, **kwargs):

        super(CreateTablesOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id = redshift_conn_id

    def execute(self, context):
        redshift = PostgresHook(self.redshift_conn_id)

        self.log.info("Creating Redshift tables ")

        sql_file = open(CreateTablesOperator.sql_file, 'r').read()
        sql_commands = sql_file.split(';')

        for command in sql_commands:
            if command.rstrip() != '':
                redshift.run(command)
  