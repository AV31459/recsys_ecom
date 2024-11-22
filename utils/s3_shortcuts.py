import os
import sys

import boto3
from dotenv import load_dotenv


def check_s3_credentials_in_environment():
    """
    Checks if all necessary S3 credentials are set in environment.

    A ValueError exception is raised if some of the following variables are
    missing in environment:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - S3_BUCKET_NAME
        - S3_ENDPOINT_URL
    """

    load_dotenv()
    for var_name in (
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME',
        'S3_ENDPOINT_URL'
    ):
        if not os.getenv(var_name):
            raise ValueError(f'The variable {var_name} is not set '
                             'in environment')


def get_client_and_bucket():
    """
    Returns boto3.client object and bucket_name according to credentials
    set in environment.
    """

    # Проверяем креды
    check_s3_credentials_in_environment()

    return (
        boto3.client(
            service_name='s3',
            endpoint_url=os.getenv('S3_ENDPOINT_URL'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        ),
        os.getenv('S3_BUCKET_NAME')
    )


def print_bucket_contents(print_objects=True,
                          key_pattern='',
                          file=sys.stdout):
    """
    Print contents of S3 bucket to a file (sys.stdout by default).

    NB: S3 bucket credentials should be set in environment.
    """

    s3, bucket_name = get_client_and_bucket()
    total_size_bytes = 0

    print(f"Contents of bucket '{bucket_name}'", file=file)
    if print_objects and key_pattern:
        print(f'Using pattern "{key_pattern}" to filter displayed objects')
    if print_objects:
        print("-" * 40, file=file)
        print(f"{'File Name':<50} {'Size (MB)':>15}", file=file)
        print("-" * 40, file=file)

    objects = s3.list_objects_v2(Bucket=bucket_name)['Contents']
    for obj in objects:
        file_size_gb = obj['Size'] / (1024 ** 2)  # Convert bytes to MB
        total_size_bytes += obj['Size']
        if print_objects and key_pattern in obj['Key']:
            print(f"{obj['Key']:<50} {file_size_gb:>15.2f} MB", file=file)

    print("-" * 40)
    total_size_gb = total_size_bytes / (1024 ** 3)  # Convert bytes to GB
    print(f"Total {len(objects)} objects, size: {total_size_gb:.2f} GB",
          file=file)


def upload_file_to_s3(local_file, s3_key):
    """Uploads file to S3 bucket."""

    s3_client, bucket_name = get_client_and_bucket()

    s3_client.upload_file(
        Filename=local_file,
        Bucket=bucket_name,
        Key=s3_key
    )


def delete_file_from_s3(s3_key):
    """Deletes object (file) from s3 bucket."""

    s3_client, bucket_name = get_client_and_bucket()

    s3_client.delete_object(
        Bucket=bucket_name,
        Key=s3_key
    )


def download_file_from_s3(local_file, s3_key):
    """Downloads file from s3 storage."""

    s3_client, bucket_name = get_client_and_bucket()

    s3_client.download_file(
        Bucket=bucket_name,
        Key=s3_key,
        Filename=local_file
    )


if __name__ == '__main__':
    load_dotenv()
    print_bucket_contents(print_objects=False)
