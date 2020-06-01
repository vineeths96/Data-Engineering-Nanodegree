# Data dictionary

## About
This file contains an overview of the attributes (columns), types and descriptions for all tables used in the project.

### Tables

#### Staging Tweets

| Column | Type | Description |
| --- | --- | --- |
| user_id | VARCHAR | ID of Twitter user|
| name | VARCHAR | "Real" name of the Twitter user, e.g. Vineeth S |
| nickname | VARCHAR | Screen name of the Twitter user, e.g. @vineeths96 |
| description | VARCHAR | Bio of the Twitter user |
| user_location | VARCHAR | Location of the Twitter user, e.g. Milan, Italy |
| followers_count | INT | Number of followers for the Twitter user |
| tweets_count | INT | Number of tweets of the Twitter user |
| user_date | TIMESTAMP | Date when the Twitter user was created |
| verified | BOOL | Whether the user is verified (blue check sign) |
| tweet_id | VARCHAR | ID of tweet|
| text | VARCHAR | Text of tweet|
| favs | INT | Number of times the tweet is marked as favorite by other Twitter users |
| retweets | INT | Number of times the tweet is re-tweeted by other Twitter users |
| tweet_date | TIMESTAMP | Date when tweet was created|
| tweet_location | VARCHAR | Location where the tweet was send from (if available)|
| source | VARCHAR | Device/App used to create the tweet, e.g. Twitter for Android/iPhone, Twitter for Desktop, etc.|
| sentiment | VARCHAR | Sentiment of the tweet text as determined by AWS Comprehend (positive/neutral/negative) |

#### Staging Happiness

| Column | Type | Description |
| --- | --- | --- |
| country | VARCHAR | Name of the country |
| rank | INT | Position of the country in happiness ranking |
| score | DECIMAL | Happiness score|
| confidence_high | DECIMAL | Upper bound of confidence interval for happiness score |
| confidence_low | DECIMAL | Lower bound of confidence Interval for happiness score |
| economy | DECIMAL | Contribution of economic situation to happiness score|
| family | DECIMAL | Contribution of family situation to happiness score|
| health | DECIMAL | Contribution of life expectancy to happiness score|
| freedom | DECIMAL | Contribution of personal/collective freedom to happiness score|
| trust | DECIMAL | Contribution of corruption into situation to happiness score |
| generosity | DECIMAL | Contribution of perceived generosity to happiness score|
| dystopia | DECIMAL | Contribution of dystopia to happiness score|

#### Staging Temperature

| Column | Type | Description |
| --- | --- | --- |
|date | TIMESTAMP | Date when the temperature was recorded|
|temperature | DECIMAL | Average temperature measured at recording date|
|uncertainty | DECIMAL | 95% confidence interval around average temperature |
|country | VARCHAR | Country where temperature was recorded|

#### Users
| Column | Type | Description |
| --- | --- | --- |
| user_id | VARCHAR | ID of Twitter user |
| name | VARCHAR | "Real" name of the Twitter user, e.g. Vineeth S |
| nickname | VARCHAR | Screen name of the Twitter user, e.g. @vineeths96 |
| description | VARCHAR | Bio of the Twitter user |
| location | VARCHAR | Location of the Twitter user, e.g. Milan, Italy |
| followers_count | INT | Number of followers for the Twitter user |
| tweets_count | INT | Number of tweets of the Twitter user |
| creation_date | TIMESTAMP | Date when the Twitter user was created |
| is_verified | BOOL | Whether the user is verified (blue check sign) |

#### Sources
| Column | Type | Description |
| --- | --- | --- |
|source_id | BIGINT | Auto-incrementing ID of sources|
|source | VARCHAR | Device/App used to create the tweet, e.g. Twitter for Android/iPhone, Twitter for Desktop, etc. |
|is_mobile | BOOL | Whether the source is a mobile device|
|is_from_twitter | BOOL | Whether the source is made by Twitter or a third-party app, e.g. Tweetdeck|

#### Happiness
| Column | Type | Description |
| --- | --- | ---|
| country | VARCHAR | Name of the country |
| rank | INT | Position of the country in happiness ranking |
| score | DECIMAL | Happiness score |
| economy | DECIMAL | Contribution of economic situation to happiness score |
| family | DECIMAL | Contribution of family situation to happiness score |
| health | DECIMAL | Contribution of life expectancy to happiness score |
| freedom | DECIMAL | Contribution of personal/collective freedom to happiness score |
| trust | DECIMAL | Contribution of corruption into situation to happiness score |
| generosity | DECIMAL | Contribution of perceived generosity to happiness score |
| dystopia | DECIMAL | Contribution of dystopia to happiness score |

#### Temperature
| Column | Type | Description |
| --- | --- | ---|
| country | VARCHAR | Country where temperature was recorded |
| temp_last_20 | DECIMAL | Average temperature over the last 20 years|
| temp_last_50 | DECIMAL | Average temperature over the last 50 years|
| temp_last_100 | DECIMAL | Average temperature over the last 100 years|

#### Time
| Column | Type | Description |
| --- | --- | ---|
| date | TIMESTAMP | Union of distinct TIMESTAMPs from user_date and tweet_date found in staging_tweets|
| second | INT | Second derived from date|
| minute | INT | Minute derived from date|
| hour | INT | Hour derived from date|
| week | INT | Calendar week derived from date|
| month | VARCHAR | Month derived from date|
| year | INT | Year derived from date|
| weekday | VARCHAR | Weekday derived from date|

#### Tweets
| Column | Type | Description |
| --- | --- | ---|
| tweet_id | VARCHAR | ID of tweet |
| sentiment | VARCHAR | Sentiment of the tweet text as determined by AWS Comprehend (positive/neutral/negative) |
| text | VARCHAR | Text of tweet |
| favs | INT | Number of times the tweet is marked as favorite by other Twitter users |
| retweets | INT | Number of times the tweet is re-tweeted by other Twitter users |
| creation_date | TIMESTAMP | Date when tweet was created |
| location | VARCHAR | Location of the Twitter user, e.g. Milan, Italy |
| user_id | VARCHAR | ID of Twitter user |
| source | VARCHAR | Device/App used to create the tweet, e.g. Twitter for Android/iPhone, Twitter for Desktop, etc. |
| happy_rank | INT | Happiness rank of country from user who created the tweet|
| happy_score | INT | Happiness score of country from user who created the tweet|
| temp_last_20 | DECIMAL | Average temperature over last 20 years of country from user who created the tweet|
| temp_last_50 | DECIMAL | Average temperature over last 50 years of country from user who created the tweet|
| temp_last_100 | DECIMAL | Average temperature over last 100 years of country from user who created the tweet|
