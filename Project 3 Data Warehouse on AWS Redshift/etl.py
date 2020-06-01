import configparser
import psycopg2
from sql_queries import copy_table_queries, insert_table_queries


def load_staging_tables(cur, conn):
    """
    Load data from files stored in S3 to the staging tables.
    """
    
    print("Loading data from JSON files stored in S3 buckets into staging tables")
    
    for query in copy_table_queries:
        cur.execute(query)
        conn.commit()
    
    print("Complete.\n")


def insert_tables(cur, conn):
    """
    Insert data from staging tables into the tables.
    """
    
    print("Inserting data from staging tables into Redshift tables")
    
    for query in insert_table_queries:
        cur.execute(query)
        conn.commit()

    print("Complete.\n")
    

def main():
    """
    Extract song metadata and user activity data from S3, transform it using a staging table, and load it into fact and dimensional tables for analysis
    """
    
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    load_staging_tables(cur, conn)
    insert_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()