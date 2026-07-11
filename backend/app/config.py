"""Centralised configuration read from environment variables.

Local dev loads these from a .env file (via python-dotenv if present); in Lambda
they come from the function's environment / SSM.
"""
import functools
import os

# Load .env for local dev only. In Lambda (AWS_LAMBDA_FUNCTION_NAME is set) we must
# NOT read a bundled .env — it would override real env vars (e.g. point DynamoDB at
# localhost or use the dev JWT secret).
if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:  # pragma: no cover
        pass

import boto3


AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DYNAMODB_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL") or None
USERS_TABLE = os.environ.get("USERS_TABLE", "Users")
BULLETS_TABLE = os.environ.get("BULLETS_TABLE", "ResumeBullets")

JWT_SECRET_PARAM = os.environ.get("JWT_SECRET_PARAM")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))

BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")


@functools.lru_cache(maxsize=1)
def get_jwt_secret() -> str:
    """Return the JWT signing secret.

    Prefers a direct JWT_SECRET env var (local dev). In prod, JWT_SECRET is left
    unset and the value is pulled once from SSM Parameter Store.
    """
    direct = os.environ.get("JWT_SECRET")
    if direct:
        return direct
    if JWT_SECRET_PARAM:
        ssm = boto3.client("ssm", region_name=AWS_REGION)
        resp = ssm.get_parameter(Name=JWT_SECRET_PARAM, WithDecryption=True)
        return resp["Parameter"]["Value"]
    raise RuntimeError("No JWT secret configured: set JWT_SECRET or JWT_SECRET_PARAM")
