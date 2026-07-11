"""Create the Users and ResumeBullets tables.

Intended for DynamoDB Local (points at DYNAMODB_ENDPOINT_URL). In AWS the tables
are provisioned by the SAM template instead. Idempotent: skips tables that exist.

Usage:
    python -m scripts.create_tables
"""
import sys

import boto3
from botocore.exceptions import ClientError

# Allow running as a script from backend/
sys.path.insert(0, ".")
from app import config  # noqa: E402


def _client():
    kwargs = {"region_name": config.AWS_REGION}
    if config.DYNAMODB_ENDPOINT_URL:
        kwargs["endpoint_url"] = config.DYNAMODB_ENDPOINT_URL
    return boto3.client("dynamodb", **kwargs)


def _create(client, **kwargs):
    name = kwargs["TableName"]
    try:
        client.create_table(BillingMode="PAY_PER_REQUEST", **kwargs)
        print(f"created table {name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"table {name} already exists, skipping")
        else:
            raise


def main():
    client = _client()
    _create(
        client,
        TableName=config.USERS_TABLE,
        AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
    )
    _create(
        client,
        TableName=config.BULLETS_TABLE,
        AttributeDefinitions=[
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "bullet_id", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "user_id", "KeyType": "HASH"},
            {"AttributeName": "bullet_id", "KeyType": "RANGE"},
        ],
    )
    print("done")


if __name__ == "__main__":
    main()
