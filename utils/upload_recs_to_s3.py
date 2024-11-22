from dotenv import load_dotenv
from s3_shortcuts import print_bucket_contents, upload_file_to_s3


def main():
    """Convenience function to upload files to s3."""

    load_dotenv()

    files = [
        'prod_build/recs/top_popular.parquet',
        'prod_build/recs/weighted_als.parquet',
        'prod_build/recs/items_train.parquet',
        'data/category_tree.csv',
        'data/events.csv',
        'data/item_properties_part1.csv',
        'data/item_properties_part2.csv',
    ]
    s3_prefix = 'final_project/'

    for file in files:
        s3_key = s3_prefix + file
        print(f"Uploading local '{file}' to S3 key '{s3_key}'")
        upload_file_to_s3(file, s3_key)

    print_bucket_contents(key_pattern=s3_prefix)


if __name__ == '__main__':
    main()
