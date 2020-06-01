import os
import configparser
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.functions import year, month, dayofmonth, hour, weekofyear, date_format
from pyspark.sql.functions import monotonically_increasing_id
from pyspark.sql.types import StructType as R, StructField as Fld, DoubleType as Dbl
from pyspark.sql.types import StringType as Str, IntegerType as Int, DateType as Dat, TimestampType


config = configparser.ConfigParser()
config.read('dl.cfg')

os.environ['AWS_ACCESS_KEY_ID']=config.get('AWS', 'AWS_ACCESS_KEY_ID')
os.environ['AWS_SECRET_ACCESS_KEY']=config.get('AWS', 'AWS_SECRET_ACCESS_KEY')


def create_spark_session():
    """
    Creates a new Spark session with the specified configuration or retrieves 
    the existing spark session and update the configuration
    
    :return spark: Spark session
    """
    
    spark = SparkSession \
            .builder \
            .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:2.7.0") \
            .getOrCreate()
    
    return spark


def process_song_data(spark, input_data, output_data):
    """
    Loads the song_data from AWS S3 (input_data) and extracts the songs and artist tables
    and then loaded the processed data back to S3 (output_data)
    
    :param spark: Spark Session object
    :param input_data: Location (AWS S3 path) of songs metadata (song_data) JSON files
    :param output_data: Location (AWS S3 path) where dimensional tables will be stored in parquet format 
    """
    
    # Get filepath to song data file
    song_data = input_data + "song_data/*/*/*/*.json"
            
    songSchema = R([
        Fld("artist_id", Str()),
        Fld("artist_latitude", Dbl()),
        Fld("artist_location", Str()),
        Fld("artist_longitude", Dbl()),
        Fld("artist_name", Str()),
        Fld("duration", Dbl()),
        Fld("num_songs", Int()),
        Fld("title", Str()),
        Fld("year", Int()),
    ])
    
    # Read song data file
    print("Reading song_data JSON files from S3")
    df = spark.read.json(song_data, mode='PERMISSIVE', schema=songSchema, \
                         columnNameOfCorruptRecord='corrupt_record').dropDuplicates()
    print("Read completed")
    
    # Extract columns to create songs table
    songs_table = df.select("title", "artist_id", "year", "duration").dropDuplicates() \
                    .withColumn("song_id", monotonically_increasing_id())

    print("Writing Songs table to S3 after processing")
    # Write songs table to parquet files partitioned by year and artist
    songs_table.write.parquet(output_data + "songs/", mode="overwrite", partitionBy=["year","artist_id"])
    print("Completed")
    
    # Extract columns to create artists table
    artists_table = df.select("artist_id", "artist_name", "artist_location", "artist_latitude", "artist_longitude") \
                        .dropDuplicates()

    print("Writing Artists table to S3 after processing")
    # Write artists table to parquet files
    artists_table.write.parquet(output_data + "artists/", mode="overwrite")
    print("Completed")
    

def process_log_data(spark, input_data, output_data):
    """
    Loads the log_data from AWS S3 (input_data) and extracts the songs and artist tables
    and then loaded the processed data back to S3 (output_data)
    
    :param spark: Spark Session object
    :param input_data: Location (AWS S3 path) of songs metadata (song_data) JSON files
    :param output_data: Location (AWS S3 path) where dimensional tables will be stored in parquet format             
    """
    
    # Ret filepath to log data file
    log_data = input_data + 'log_data/*/*/*.json'

    # Read log data file
    print("Reading log_data JSON files from S3")
    df = spark.read.json(log_data)
    print("Read completed")
    
    # Filter by actions for song plays
    df = df.filter(df.page == 'NextSong')

    # Extract columns for users table  
    users_table = df.select("userId", "firstName", "lastName", "gender", "level").dropDuplicates()

    # Write users table to parquet files
    print("Writing Users table to S3 after processing")  
    users_table.write.parquet(os.path.join(output_data, "users/") , mode="overwrite")
    print("Completed")
    
    # Create timestamp column from original timestamp column
    get_timestamp = udf(lambda x : datetime.utcfromtimestamp(int(x) / 1000), TimestampType())
    df = df.withColumn("start_time", get_timestamp("ts"))
    
    # Extract columns to create time table
    time_table = df.withColumn("hour", hour("start_time")) \
                   .withColumn("day", dayofmonth("start_time")) \
                   .withColumn("week", weekofyear("start_time")) \
                   .withColumn("month", month("start_time")) \
                   .withColumn("year", year("start_time")) \
                   .withColumn("weekday", dayofweek("start_time")) \
                   .select("ts", "start_time", "hour", "day", "week", "month", "year", "weekday") \
                   .drop_duplicates()

    # Write time table to parquet files partitioned by year and month
    print("Writing Time table to S3 after processing")  
    time_table.write.parquet(os.path.join(output_data, "time_table/"), mode='overwrite', \
                             partitionBy=["year","month"])
    print("Completed")
    
    # Read in song data to use for songplays table
    song_df = spark.read \
                .format("parquet") \
                .option("basePath", os.path.join(output_data, "songs/")) \
                .load(os.path.join(output_data, "songs/*/*/"))

    # Extract columns from joined song and log datasets to create songplays table
    songplays_table = df.join(song_df, df.song == song_df.title, how='inner') \
                        .select(monotonically_increasing_id().alias("songplay_id"), \
                                col("start_time"), \
                                col("userId").alias("user_id"), \
                                "level","song_id","artist_id", \
                                col("sessionId").alias("session_id"), \
                                "location", \
                                col("userAgent").alias("user_agent"))

    songplays_table = songplays_table.join(time_table, songplays_table.start_time == time_table.start_time, how="inner") \
                        .select("songplay_id", songplays_table.start_time, "user_id", "level", "song_id", \
                                "artist_id", "session_id", "location", "user_agent", "year", "month").drop_duplicates()

    # Write songplays table to parquet files partitioned by year and month
    print("Writing Songplays table to S3 after processing")  
    songplays_table.write.parquet(os.path.join(output_data, "songplays/"), \
                                  mode="overwrite", partitionBy=["year","month"])
    print("Completed")


def main():
    spark = create_spark_session()
    input_data = "s3a://udacity-dend/"
    output_data = "s3a://sparkify-udacity/"
    
    print("\n")
    
    print("Processing song_data files")
    process_song_data(spark, input_data, output_data)
    print("Processing completed\n")
    
    print("Processing log_data files")
    process_log_data(spark, input_data, output_data)
    print("Processing completed\n")


if __name__ == "__main__":
    main()
