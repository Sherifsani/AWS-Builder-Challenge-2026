#!/usr/bin/env bash
#
# One-shot deploy for the Resume/CV Tailor: SAM backend (Lambda + API Gateway +
# DynamoDB + Bedrock IAM) and the Vite frontend to an S3 static website.
#
# Idempotent and non-interactive — safe to run repeatedly. First run creates
# everything; later runs update in place.
#
# Usage:
#   ./deploy.sh                 # deploy backend + frontend
#   ./deploy.sh backend         # backend only
#   ./deploy.sh frontend        # frontend only (backend must already exist)
#
# Override defaults via env vars, e.g.:
#   REGION=us-west-2 STACK_NAME=my-stack BUCKET=my-bucket ./deploy.sh
#
set -euo pipefail

# ---- Config (override via environment) --------------------------------------
REGION="${REGION:-us-east-1}"
STACK_NAME="${STACK_NAME:-resume-tailor}"
JWT_PARAM="${JWT_PARAM:-/resume-tailor/jwt-secret}"
# Bucket names are globally unique; default appends the account id.
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
BUCKET="${BUCKET:-resume-tailor-${ACCOUNT_ID}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

TARGET="${1:-all}"

log()  { printf '\n\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

# ---- Prerequisite checks ----------------------------------------------------
check_prereqs() {
  command -v aws >/dev/null || die "aws CLI not found"
  aws sts get-caller-identity >/dev/null 2>&1 || die "AWS credentials not configured (run: aws configure)"
  if [ "$TARGET" != "frontend" ]; then
    command -v sam >/dev/null || die "SAM CLI not found — install it, then re-run"
  fi
  if [ "$TARGET" != "backend" ]; then
    command -v npm >/dev/null || die "npm not found"
  fi
}

# ---- Backend ----------------------------------------------------------------
ensure_jwt_secret() {
  if aws ssm get-parameter --name "$JWT_PARAM" --region "$REGION" >/dev/null 2>&1; then
    log "JWT secret $JWT_PARAM already exists — leaving it."
  else
    log "Creating JWT signing secret in SSM ($JWT_PARAM)"
    aws ssm put-parameter --name "$JWT_PARAM" --type SecureString \
      --value "$(openssl rand -hex 32)" --region "$REGION" >/dev/null
  fi
}

check_bedrock_access() {
  # Best-effort warning; a full check needs a live invoke. Just remind.
  warn "Ensure Amazon Nova Lite model access is ENABLED in Bedrock ($REGION),"
  warn "or /match and /generate-cv will fail with AccessDeniedException."
}

deploy_backend() {
  ensure_jwt_secret
  check_bedrock_access
  log "Building backend (sam build)"
  ( cd "$BACKEND_DIR" && sam build )
  log "Deploying stack '$STACK_NAME' to $REGION"
  ( cd "$BACKEND_DIR" && sam deploy \
      --stack-name "$STACK_NAME" \
      --region "$REGION" \
      --capabilities CAPABILITY_IAM \
      --resolve-s3 \
      --no-confirm-changeset \
      --no-fail-on-empty-changeset \
      --parameter-overrides "JwtSecretParam=$JWT_PARAM" )
}

api_base_url() {
  aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiBaseUrl'].OutputValue" --output text
}

# ---- Frontend ---------------------------------------------------------------
ensure_bucket() {
  if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
    log "Bucket s3://$BUCKET already exists"
  else
    log "Creating bucket s3://$BUCKET"
    if [ "$REGION" = "us-east-1" ]; then
      aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" >/dev/null
    else
      aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
    fi
  fi

  log "Allowing public read (disabling block-public-access + bucket policy)"
  aws s3api put-public-access-block --bucket "$BUCKET" \
    --public-access-block-configuration \
    BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

  aws s3api put-bucket-policy --bucket "$BUCKET" --policy "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Sid\": \"PublicReadGetObject\",
      \"Effect\": \"Allow\",
      \"Principal\": \"*\",
      \"Action\": \"s3:GetObject\",
      \"Resource\": \"arn:aws:s3:::$BUCKET/*\"
    }]
  }"

  aws s3 website "s3://$BUCKET/" --index-document index.html --error-document index.html
}

deploy_frontend() {
  local url
  url="$(api_base_url)"
  [ -n "$url" ] && [ "$url" != "None" ] || die "Could not read ApiBaseUrl — deploy the backend first."
  log "Pointing frontend at API: $url"
  printf 'VITE_API_BASE_URL=%s\n' "$url" > "$FRONTEND_DIR/.env.production"

  log "Building frontend"
  ( cd "$FRONTEND_DIR" && npm install --no-audit --no-fund && npm run build )

  ensure_bucket

  log "Uploading dist/ to s3://$BUCKET"
  aws s3 sync "$FRONTEND_DIR/dist/" "s3://$BUCKET" --delete

  log "Done. Site: http://$BUCKET.s3-website-$REGION.amazonaws.com"
}

# ---- Main -------------------------------------------------------------------
check_prereqs
case "$TARGET" in
  backend)  deploy_backend ;;
  frontend) deploy_frontend ;;
  all)      deploy_backend; deploy_frontend ;;
  *)        die "Unknown target '$TARGET' (use: all | backend | frontend)" ;;
esac

log "Deployment complete."
echo "  API:  $(api_base_url 2>/dev/null || echo 'n/a')"
echo "  Site: http://$BUCKET.s3-website-$REGION.amazonaws.com"
