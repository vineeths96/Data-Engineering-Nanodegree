from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults


class LoadDimensionOperator(BaseOperator):
    """
    Airflow Operator to load data into dimensional tables from staging events and song
    data. Optional parameter 'truncate' can be set to empty target tables prior to load
    """

    ui_color = '#80BD9E'

    @apply_defaults
    def __init__(self,
                 redshift_conn_id="",
                 sql_query="",
                 table="",
                 truncate=False,
                 *args, **kwargs):
        
        super(LoadDimensionOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id = redshift_conn_id
        self.sql_query = sql_query
        self.table = table
        self.truncate = truncate

    def execute(self, context):
        redshift = PostgresHook(self.redshift_conn_id)
        
        if self.truncate:
            self.log.info("Truncating table before inserting new data...")
            redshift.run(f"TRUNCATE TABLE {self.table}")
        
        self.log.info("Inserting data to dimension table...")
        formatted_sql = self.sql_query.format(self.table)
        redshift.run(formatted_sql)
        self.log.info(f"Success: {self.task_id}")
