#!/usr/bin/env bash
# ==============================================================================
# Google Cloud Platform Infrastructure Setup Script
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${2:-us-central1}"
TYPESAFE_KEY_INPUT="${3:-}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "❌ Error: Project ID not provided."
  echo "Usage: ./scripts/setup_gcp.sh <PROJECT_ID> [REGION] [TYPESAFE_API_KEY]"
  exit 1
fi

echo "🚀 Configuring Google Cloud project: ${PROJECT_ID} in ${REGION}"
gcloud config set project "${PROJECT_ID}"

echo "📦 1. Enabling required Google Cloud APIs..."
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

echo "🔐 2. Configuring TypeSafe API Key in Secret Manager..."
if ! gcloud secrets describe typesafe-api-key --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud secrets create typesafe-api-key \
    --replication-policy="automatic" \
    --project="${PROJECT_ID}"
  echo "✅ Created secret 'typesafe-api-key'."
else
  echo "ℹ️ Secret 'typesafe-api-key' already exists."
fi

if [[ -n "${TYPESAFE_KEY_INPUT}" ]]; then
  echo -n "${TYPESAFE_KEY_INPUT}" | gcloud secrets versions add typesafe-api-key --data-file=- --project="${PROJECT_ID}"
  echo "✅ Added secret version for 'typesafe-api-key'."
else
  echo "⚠️ Note: No TypeSafe API key passed. Secret created without payload. (Run 'echo -n KEY | gcloud secrets versions add typesafe-api-key --data-file=-' when ready)."
fi

echo "👤 3. Creating dedicated Least-Privilege Service Account..."
SA_NAME="hybrid-gateway-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="Hybrid AI Gateway Cloud Run Identity" \
    --project="${PROJECT_ID}"
  echo "✅ Created service account: ${SA_EMAIL}"
else
  echo "ℹ️ Service account ${SA_EMAIL} already exists."
fi

echo "🛡️ 4. Binding IAM Roles..."
# Gemini Enterprise Agent Platform User (to invoke Gemini models)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user" \
  --condition=None

# Secret Accessor (to read TypeSafe API key)
gcloud secrets add-iam-policy-binding typesafe-api-key \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" \
  --project="${PROJECT_ID}"

# BigQuery Data Editor (for telemetry)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.dataEditor" \
  --condition=None

echo "🐳 5. Creating Artifact Registry repository..."
REPO_NAME="ai-gateway-repo"
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Docker repo for Hybrid AI Gateway" \
    --project="${PROJECT_ID}"
  echo "✅ Created Artifact Registry repo: ${REPO_NAME}"
else
  echo "ℹ️ Artifact Registry repo ${REPO_NAME} already exists."
fi

echo "📊 6. Initializing BigQuery Telemetry Dataset..."
bq --location=US mk --dataset --if_exists "${PROJECT_ID}:ai_gateway_telemetry" || true
bq query --use_legacy_sql=false < sql/bigquery_schema.sql || true

echo ""
echo "🎉 Google Cloud Setup Completed Successfully!"
echo "Service Account: ${SA_EMAIL}"
echo "Next step: Run ./scripts/deploy.sh ${PROJECT_ID} ${REGION}"
