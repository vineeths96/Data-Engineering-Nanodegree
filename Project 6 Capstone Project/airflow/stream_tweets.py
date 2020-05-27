import boto3
import logging
from configparser import ConfigParser
from botocore.exceptions import ClientError
from tweepy import StreamListener, Stream, OAuthHandler


class TweetListener(StreamListener):
    """
    Streams the recent tweets related to the query to AWS Kinesis
    """

    def __init__(self, config):
        super(StreamListener, self).__init__()

        # Set up AWS configurations
        self.config = config
        self.aws_access_key_id = self.config.get("AWS", "ACCESS_KEY_ID")
        self.aws_secret_access_key = self.config.get("AWS", "SECRET_ACCESS_KEY")
        self.delivery_stream = self.config.get("KINESIS", "DELIVERY_STREAM")
        self.firehose_client = boto3.client("firehose",
                                            aws_access_key_id=self.aws_access_key_id,
                                            aws_secret_access_key=self.aws_secret_access_key)

    def on_data(self, tweet):
        """
        Pushes tweets to AWS Kinesis.
        :param tweet: Tweet data (dictionary)
        :return:
        """

        try:
            # Start logging
            logging.info("Streaming tweet data to AWS Kinesis")

            # Push the record
            response = self.firehose_client.put_record(DeliveryStreamName=self.delivery_stream,
                                                       Record={"Data": tweet})

            logging.debug(response)

            return True

        except ClientError as ex:
            # In case of client error log the error
            logging.exception(f"Failed to stream tweet data to AWS Kinesis: {ex}.")

    def on_error(self, status_code):
        """
        Handle errors and exceptions
        :param status_code: HTTP status code
        :return:
        """

        # Log the error status code
        logging.error(status_code)

        # Rate limit status is not considered as error
        if status_code == 420:
            return False


def main():
    # Read config settings
    config = ConfigParser()
    config.read('../config.cfg')

    # Start logging
    logging.basicConfig(level=config.get("LOGGING", "LEVEL"), format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Started logging")

    # Authenticating twitter API
    logging.info("Authenticating Twitter API")
    auth = OAuthHandler(config.get("TWITTER", "CONSUMER_KEY"), config.get("TWITTER", "CONSUMER_SECRET"))
    auth.set_access_token(config.get("TWITTER", "ACCESS_TOKEN"), config.get("TWITTER", "ACCESS_TOKEN_SECRET"))

    # Start streaming to AWS Kinesis
    logging.info(f"Start streaming tweets matching: {config.getlist('TWEEPY', 'TRACK_TOPICS')}")

    twitter_stream = Stream(auth, TweetListener(config))
    twitter_stream.filter(track=config.getlist("TWEEPY", "TRACK_TOPICS"),
                          languages=config.getlist("TWEEPY", "TRACK_LANGS"))


if __name__ == "__main__":
    main()
