import time
import json
import boto3
import tweepy
import logging
from configparser import ConfigParser
from botocore.exceptions import ClientError


class TweetHandler:
    """
    Searches and filters historical tweets and streams them to AWS Kinesis.
    """

    def __init__(self, config):
        self.config = config

        # Set up variables
        self.limit = self.config.getint("TWEEPY", "LIMIT")
        self.logging_interval = self.config.getint("LOGGING", "INTERVAL")
        self.counter = 0
        self._batch = []

        # Set up AWS configurations
        self.aws_access_key_id = self.config.get("AWS", "ACCESS_KEY_ID")
        self.aws_secret_access_key = self.config.get("AWS", "SECRET_ACCESS_KEY")
        self.delivery_stream = self.config.get("KINESIS", "DELIVERY_STREAM")

        self.batch_size = self.config.getint("KINESIS", "BATCH_SIZE")
        self.comprehend_client = boto3.client("comprehend",
                                              aws_access_key_id=self.aws_access_key_id,
                                              aws_secret_access_key=self.aws_secret_access_key)

        self.firehose_client = boto3.client("firehose",
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key)

    def filter(self, tweet: dict) -> dict:
        """
        Filter required fields from tweet data and return it as dict
        :param tweet: Tweet data (dict)
        :return: Filtered tweet (data)
        """

        # Filter required fields
        filtered_tweet = {"user_id": tweet.user.id_str,
                          "name": tweet.user.name,
                          "nickname": tweet.user.screen_name,
                          "description": tweet.user.description,
                          "user_location": tweet.user.location,
                          "followers_count": tweet.user.followers_count,
                          "tweets_count": tweet.user.statuses_count,
                          "user_date": tweet.user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                          "verified": tweet.user.verified,
                          "tweet_id": tweet.id_str,
                          "text": tweet.full_text,
                          "favs": tweet.favorite_count,
                          "retweets": tweet.retweet_count,
                          "tweet_date": tweet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                          "tweet_location": tweet.place.full_name if tweet.place else None,
                          "source": tweet.source,
                          "sentiment": self.detect_sentiment(tweet.full_text, tweet.lang)}

        return filtered_tweet

    def detect_sentiment(self, text: str, lang: str, full_result: bool = False):
        """
        Extract the sentiment of a tweet using AWS Comprehend
        :param text: Text of tweet
        :param lang: Language of tweet (en, fr etc)
        :param full_result: Flag to return all data returned by AWS Comprehend or just the sentiment
        :return: Sentiment as str or full result as a dict (specified by full_result flag)
        """

        # Get sentiment analysis from AWS Comprehend
        sentiment = self.comprehend_client.detect_sentiment(Text=text, LanguageCode=lang)

        if full_result:
            return sentiment
        else:
            return sentiment["Sentiment"]

    @staticmethod
    def handle_rate_limit(cursor: tweepy.Cursor):
        """
        If Twitter API rate limit is exceeded (180 calls in 15 minutes), wait for 15 minutes before continuing
        :param cursor: Tweepy cursor
        :return:
        """

        while True:
            try:
                yield cursor.next()

            except tweepy.RateLimitError:
                # Pause for 15 minutes
                logging.warning("Twitter API rate limit exceeded, waiting for 15 minutes before continuing.")
                time.sleep(15 * 60)

    def process(self, cursor: tweepy.Cursor):
        """
        Stream a single filtered tweet to AWS Kinesis stream
        :param cursor: Tweepy cursor
        """

        # Start logging
        logging.info("Processing tweets")

        for tweet in self.handle_rate_limit(cursor.items(self.limit)):
            # Filter tweet
            filtered_tweet = self.filter(tweet)

            # Stream filtered tweet to AWS Kinesis
            try:
                logging.debug("Streaming tweet data to Kinesis")
                response = self.firehose_client.put_record(DeliveryStreamName=self.delivery_stream,
                                                           Record={"Data": json.dumps(filtered_tweet)})

                logging.debug(response)

            except ClientError as ex:
                # In case of client error log the error
                logging.exception(f"Failed to stream tweet data to AWS Kinesis: {ex}.")

            finally:
                self.counter += 1

                if self.counter % self.logging_interval == 0:
                    logging.info(f"Processed {self.counter} tweets.")

    def process_batch(self, cursor: tweepy.Cursor):
        """
        Stream a batach of filtered tweet to AWS Kinesis stream
        :param cursor: Tweepy Cursor
        """

        # Start logging
        logging.info("Processing tweets.")

        for tweet in self.handle_rate_limit(cursor.items(self.limit)):
            # If number of tweets less than batch size, append it. Else stream it.
            if len(self._batch) < self.batch_size:
                self._batch.append(self.filter(tweet))
            else:
                self.submit_batch(self._batch)

        # If rate limit exceeded, stream remaining tweets if any
        if self._batch:
            self.submit_batch(self._batch)

    def submit_batch(self, batch: list):
        """
        Streams a batch of filtered tweets to AWS Kinesis
        :param batch: List of tweets
        """

        try:
            logging.info(f"Streaming batch of {len(batch)} tweets to AWS Kinesis.")

            response = self.firehose_client.put_record_batch(DeliveryStreamName=self.delivery_stream,
                                                             Records=[{"Data": json.dumps(batch)}])

            logging.debug(response)

        except ClientError as ex:
            # In case of client error log the error
            logging.exception(f"Failed to stream tweet batch to AWS Kinesis: {ex}.")

        finally:
            self.counter += len(batch)
            self._batch = []


def main():
    # Read config settings
    config = ConfigParser()
    config.read('../config.cfg')

    # Start logging
    logging.basicConfig(level=config.get("LOGGING", "LEVEL"), format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Started logging.")

    # Start timer
    start_time = time.perf_counter()

    # Authenticating twitter API
    logging.info("Authenticating Twitter API")
    auth = tweepy.OAuthHandler(config.get("TWITTER", "CONSUMER_KEY"), config.get("TWITTER", "CONSUMER_SECRET"))
    auth.set_access_token(config.get("TWITTER", "ACCESS_TOKEN"), config.get("TWITTER", "ACCESS_TOKEN_SECRET"))
    api = tweepy.API(auth)

    # search and process tweets
    logging.info(f"Searching Twitter for: {config.get('TWEEPY', 'QUERY')}")
    tweet_handler = TweetHandler(config)
    tweet_handler.process_batch(tweepy.Cursor(api.search,
                                              q=config.get("TWEEPY", "QUERY"),
                                              lang=config.get("TWEEPY", "LANG"),
                                              result_type=config.get("TWEEPY", "RESULT_TYPE"),
                                              tweet_mode=config.get("TWEEPY", "TWEET_MODE"),
                                              count=config.getint("TWEEPY", "COUNT"),
                                              until=config.get("TWEEPY", "END_DATE")))
    # Stop timer
    stop_time = time.perf_counter()
    logging.info(f"Processed {tweet_handler.counter} tweets in {(stop_time - start_time):.2f} seconds.")
    logging.info("Finished streaming.")


if __name__ == "__main__":
    main()
