import sys
import configparser
import psycopg2
from sql_queries import create_table_queries, drop_table_queries


def drop_tables(cur, conn):
    """
    Drop all the table in the Redshift cluster
    :param cur: cursor object to database connection
    :param conn: connection object to database
    """
    
    for query in drop_table_queries:
        try:
            cur.execute(query)
            conn.commit()
        except psycopg2.Error as e:
            print(e)
            conn.close()
            sys.exit(0)


def create_tables(cur, conn):
    """
    Create all the tables in the Redshift cluster
    :param cur: cursor object to database connection
    :param conn: connection object to database
    """
    
    for query in create_table_queries:
        try:
            cur.execute(query)
            conn.commit()
        except psycopg2.Error as e:
            print(e)
            conn.close()
            sys.exit(0)


def main():
    """
    Connects to the Redshift cluster and resets the tables.
    """
    
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    try:
        conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
        cur = conn.cursor()
    except Exception as e:
        print(e)

    drop_tables(cur, conn)
    create_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()