import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

S3_LOG_DATA = config.get('S3', 'LOG_DATA')
S3_LOG_JSONPATH = config.get('S3', 'LOG_JSONPATH')
S3_SONG_DATA = config.get('S3', 'SONG_DATA')
DWH_IAM_ROLE_ARN = config.get("IAM_ROLE", "ARN")

# DROP TABLES
staging_events_table_drop = "DROP TABLE IF EXISTS staging_events;"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs;"
songplay_table_drop = "DROP TABLE IF EXISTS songplays;"
user_table_drop = "DROP TABLE IF EXISTS users;"
song_table_drop = "DROP TABLE IF EXISTS songs;"
artist_table_drop = "DROP TABLE IF EXISTS artists;"
time_table_drop = "DROP TABLE IF EXISTS time;"

# CREATE TABLES

staging_events_table_create= (
    """
    CREATE TABLE staging_events 
    (
        artist VARCHAR,
        auth VARCHAR,
        firstName VARCHAR,
        gender CHAR(1),
        itemInSession INTEGER,
        lastName VARCHAR,
        length DECIMAL,
        level VARCHAR,
        location VARCHAR,
        method VARCHAR,
        page VARCHAR,
        registration FLOAT,
        sessionId INTEGER,
        song VARCHAR,
        status INTEGER,
        ts VARCHAR,
        userAgent VARCHAR,
        userId INTEGER
    );
    """
)

staging_songs_table_create = (
    """
    CREATE TABLE staging_songs 
    (
        num_songs INTEGER,
        artist_id VARCHAR,
        artist_latitude DECIMAL,
        artist_longitude DECIMAL,
        artist_location VARCHAR,
        artist_name VARCHAR,
        song_id VARCHAR,
        title VARCHAR,
        duration DECIMAL,
        year INTEGER
    );
    """
)

songplay_table_create = (
    """
    CREATE TABLE IF NOT EXISTS songplays 
    (
        songplay_id INTEGER IDENTITY(0,1) PRIMARY KEY,
        start_time TIMESTAMP NOT NULL SORTKEY,
        user_id INTEGER NOT NULL REFERENCES users(user_id),
        level VARCHAR,
        song_id VARCHAR NOT NULL REFERENCES songs(song_id),
        artist_id VARCHAR NOT NULL REFERENCES artists(artist_id),
        session_id INTEGER NOT NULL,
        location VARCHAR,
        user_agent VARCHAR
    );
    """
)

user_table_create = (
    """
    CREATE TABLE IF NOT EXISTS users
    (
        user_id INTEGER SORTKEY PRIMARY KEY,
        first_name VARCHAR NOT NULL,
        last_name VARCHAR NOT NULL,
        gender CHAR(1),
        level VARCHAR NOT NULL
    );
    """
)

song_table_create = (
    """
    CREATE TABLE IF NOT EXISTS songs
    (
        song_id VARCHAR SORTKEY PRIMARY KEY,
        title VARCHAR NOT NULL,
        artist_id VARCHAR NOT NULL DISTKEY REFERENCES artists(artist_id),
        year INTEGER NOT NULL,
        duration DECIMAL NOT NULL
    );
    """
)

artist_table_create = (
    """
    CREATE TABLE IF NOT EXISTS artists 
    (
        artist_id VARCHAR SORTKEY PRIMARY KEY,
        name VARCHAR NOT NULL,
        location VARCHAR,
        latitude DECIMAL,
        longitude DECIMAL
    );
    """
)

time_table_create = (
    """
    CREATE TABLE IF NOT EXISTS time
    (
        start_time TIMESTAMP NOT NULL PRIMARY KEY SORTKEY,
        hour NUMERIC NOT NULL,
        day NUMERIC NOT NULL,
        week NUMERIC NOT NULL,
        month NUMERIC NOT NULL,
        year NUMERIC NOT NULL,
        weekday NUMERIC NOT NULL
    );
    """
)

# STAGING TABLES

staging_events_copy = (
    """
    COPY staging_events 
    FROM {}
    iam_role '{}'
    FORMAT AS json {}
    """).format(S3_LOG_DATA, DWH_IAM_ROLE_ARN, S3_LOG_JSONPATH
)

staging_songs_copy = (
    """
    COPY staging_songs 
    FROM {}
    iam_role '{}'
    FORMAT AS json 'auto'
    """).format(S3_SONG_DATA, DWH_IAM_ROLE_ARN
)

# FINAL TABLES

songplay_table_insert = (
    """
    INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
    SELECT DISTINCT to_timestamp(to_char(e.ts, '9999-99-99 99:99:99'),'YYYY-MM-DD HH24:MI:SS') AS start_time,
        e.userId AS user_id,
        e.level AS level,
        s.song_id AS song_id,
        s.artist_id AS artist_id,
        e.sessionId AS session_id,
        e.location AS location,
        e.userAgent AS user_agent
    FROM staging_events e
    JOIN staging_songs s ON (e.song = s.title AND e.artist = s.artist_name)
    AND e.page  =  'NextSong'
    """
)

user_table_insert = (
    """
    INSERT INTO users (user_id, first_name, last_name, gender, level)
    SELECT DISTINCT(userId) AS user_id,
        firstName AS first_name,
        lastName AS last_name,
        gender,
        level
    FROM staging_events
    WHERE page = 'NextSong' 
    AND user_id NOT IN (SELECT DISTINCT user_id FROM users)
    """
)

song_table_insert = (
    """
    INSERT INTO songs (song_id, title, artist_id, year, duration)
    SELECT DISTINCT(song_id) AS song_id,
        title,
        artist_id,
        year,
        duration
    FROM staging_songs
    WHERE song_id NOT IN (SELECT DISTINCT song_id FROM songs)
    """
)

artist_table_insert = (
    """
    INSERT INTO artists (artist_id, name, location, latitude, longitude)
    SELECT DISTINCT(artist_id) as artist_id,
        artist_name AS name,
        artist_location AS location,
        artist_latitude AS latitude,
        artist_longitude AS longitude
    FROM staging_songs
    WHERE artist_id NOT IN (SELECT DISTINCT artist_id FROM artists)
    """
)

time_table_insert = (
    """
    INSERT INTO time (start_time, hour, day, week, month, year, weekday)
    SELECT DISTINCT to_timestamp(to_char(e.ts, '9999-99-99 99:99:99'),'YYYY-MM-DD HH24:MI:SS') AS start_time,
            EXTRACT(hour FROM start_time) AS hour,
            EXTRACT(day FROM start_time) AS day,
            EXTRACT(week FROM start_time) AS week,
            EXTRACT(month FROM start_time) AS month,
            EXTRACT(year FROM start_time) AS year,
            EXTRACT(dayofweek FROM start_time) as weekday
    FROM staging_events e;
    """
)

analyze_queries = [
    'SELECT COUNT(*) AS total FROM songs',
    'SELECT COUNT(*) AS total FROM songplays',
    'SELECT COUNT(*) AS total FROM artists',
    'SELECT COUNT(*) AS total FROM users',
    'SELECT COUNT(*) AS total FROM time',
    'SELECT COUNT(*) AS total FROM staging_events',
    'SELECT COUNT(*) AS total FROM staging_songs'
]

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, time_table_create, user_table_create,\
                        artist_table_create, song_table_create, songplay_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, \
                      song_table_drop, artist_table_drop, time_table_drop]

copy_table_order = ['staging_events', 'staging_songs']
copy_table_queries = [staging_events_copy, staging_songs_copy]

insert_table_order = ['artists', 'songs', 'time', 'users', 'songplays']
insert_table_queries = [artist_table_insert, song_table_insert, time_table_insert, user_table_insert, songplay_table_insert]
