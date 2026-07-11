"""DynamoDB access layer.

A single boto3 resource is created lazily and reused (important for Lambda warm
starts). When DYNAMODB_ENDPOINT_URL is set, it points at DynamoDB Local.
"""
import functools

import boto3

from . import config


@functools.lru_cache(maxsize=1)
def _resource():
    kwargs = {"region_name": config.AWS_REGION}
    if config.DYNAMODB_ENDPOINT_URL:
        kwargs["endpoint_url"] = config.DYNAMODB_ENDPOINT_URL
    return boto3.resource("dynamodb", **kwargs)


def users_table():
    return _resource().Table(config.USERS_TABLE)


def bullets_table():
    return _resource().Table(config.BULLETS_TABLE)
