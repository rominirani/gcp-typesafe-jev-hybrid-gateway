#!/usr/bin/env bash
# ==============================================================================
# Google Cloud Run Deployment Script
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${2:-us-central1}"
SERVICE_NAME="hybrid-ai-gateway"
REPO_NAME="ai-gateway-repo"
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"
SA_EMAIL="hybrid-gateway-sa@${PROJECT_ID}.iam.gserviceaccount.com"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "❌ Error: Project ID not specified."
  echo "Usage: ./scripts/deploy.sh <PROJECT_ID> [REGION]"
  exit 1
fi

echo "🚀 Building and deploying '${SERVICE_NAME}' to Google Cloud Run..."
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "Image:    ${IMAGE_TAG}"

echo "🔨 1. Submitting build to Google Cloud Build..."
gcloud builds submit --tag "${IMAGE_TAG}" --project="${PROJECT_ID}" .

echo "🚢 2. Deploying container to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE_TAG}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --platform="managed" \
  --service-account="${SA_EMAIL}" \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=10 \
  --memory="1Gi" \
  --cpu="1" \
  --concurrency=80 \
  --timeout=60s \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=global,GEMINI_MODEL=gemini-3.8-flash,CONFIDENCE_THRESHOLD=0.90,ENABLE_BIGQUERY_TELEMETRY=true" \
  --set-secrets="TYPESAFE_API_KEY=typesafe-api-key:latest"

echo ""
echo "🎉 Deployment Complete!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --project="${PROJECT_ID}" --format="value(status.url)")
echo "🌐 Service URL: ${SERVICE_URL}"
echo "Test the live dashboard by opening: ${SERVICE_URL}"
