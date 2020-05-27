import time
import boto3
import logging
from pathlib import Path
from configparser import ConfigParser
from botocore.exceptions import ClientError


def create_bucket(bucket_name: str, region: str = 'us-west-2'):
    """
    Create AWS S3 bucket (if it does not exist)
    :param bucket_name: Name of S3 bucket
    :param region: AWS region where bucket is created
    :return: True if bucket is created/already exists or False if ClientError occurs
    """

    try:
        # S3 boto3 client
        s3_client = boto3.client('s3', region=region)

        # List buckets in the region for the user
        response = s3_client.list_buckets()

        # If bucket not in the list, create the bucket
        if bucket_name not in response['Buckets']:
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            logging.warning(f"{bucket_name} already exist in AWS region {region}.")

    except ClientError as e:
        # In case of client error log the error
        logging.exception(e)

        return False

    return True


def upload_file(file_name: str, bucket: str, object_name: str = None, region: str = 'us-west-2'):
    """
    Upload the specified file to specified S3 bucket
    :param file_name: Path to file
    :param bucket: Bucket to which file has to be uploaded
    :param object_name: Name with which file has to be stored inside S3 bucket
    :param region: AWS region where bucket is located
    :return: True if upload succeeds, False if ClientError occurs
    """

    # If no object name is specified, store it with file name
    if object_name is None:
        object_name = file_name

    try:
        # Upload using the boto3 client
        s3_client = boto3.client('s3', region=region)
        s3_client.upload_file(file_name, bucket, object_name)

    except ClientError as e:
        # In case of client error log the error
        logging.exception(e)

        return False

    return True


def main():
    # Read config settings
    config = ConfigParser()
    config.read('../config.cfg')

    # Start logging
    logging.basicConfig(level=config.get("LOGGING", "LEVEL"), format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Started logging.")

    # Start timer
    start_time = time.perf_counter()

    # Path to the datasets
    data_path = Path(__file__).parent.joinpath('datasets')

    # Create bucket if it does not exist
    bucket_name = config.get("AWS", "S3_BUCKET")
    create_bucket(bucket_name=bucket_name)

    # Upload datasets to S3
    upload_file(data_path.joinpath('happiness_index.csv'), bucket=bucket_name, object_name='world_happiness.csv')
    upload_file(data_path.joinpath('temperature_city.csv'), bucket=bucket_name, object_name='temp_by_city.csv')

    # Stop timer
    stop_time = time.perf_counter()

    # Log the upload completion
    logging.info(f"Uploaded files in {(stop_time - start_time):.2f} seconds.")
    logging.info("Finished.")


if __name__ == '__main__':
    main()
