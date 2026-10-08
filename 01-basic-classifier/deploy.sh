#!/usr/bin/env bash
# ==============================================================================
# Deploy Stage 01: Standalone Jev Classifier to Cloud Run (Requires Secret Manager)
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${2:-us-central1}"
SERVICE_NAME="jev-basic-classifier"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "❌ Error: Project ID not specified."
  echo "Usage: ./deploy.sh <PROJECT_ID> [REGION]"
  exit 1
fi

echo "🚀 Deploying Stage 01 Standalone Classifier to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Region:  ${REGION}"

gcloud run deploy "${SERVICE_NAME}" \
  --source="." \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --allow-unauthenticated \
  --set-secrets="TYPESAFE_API_KEY=typesafe-api-key:latest" \
  --min-instances=0 \
  --max-instances=5 \
  --memory="512Mi" \
  --cpu="1" \
  --timeout=30s \
  --quiet

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --project="${PROJECT_ID}" --format="value(status.url)")
echo ""
echo "✅ Stage 01 Service is live!"
echo "URL: ${SERVICE_URL}"
