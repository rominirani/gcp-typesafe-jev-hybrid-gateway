# Stage 01: Standalone Jev Classification Microservice on Cloud Run

The first stepping stone in building machine-native intelligence architectures on Google Cloud: packaging **TypeSafe Jev** (`https://api.typesafe.ai/v1/systemone`) into a minimal, production-ready serverless microservice.

---

## 🌟 What This Demonstrates
* Deploying a dedicated System 1 classification microservice to **Google Cloud Run** backed by **Google Cloud Secret Manager** (`TYPESAFE_API_KEY`).
* Calling TypeSafe AI's `/v1/systemone` endpoint with `choice`, `score`, and `noul` primitives in a single parallel forward pass.
* Returning **strongly typed categories and RLCD calibrated probabilities** with mathematically zero type errors.

---

## 🚀 Service Endpoints

Once deployed, Cloud Run provides your service URL (`SERVICE_URL`):
* **Service Base URL:** `https://jev-basic-classifier-<PROJECT_NUMBER>.us-central1.run.app`
* **Interactive Swagger UI:** `${SERVICE_URL}/docs`
* **Health Check:** `${SERVICE_URL}/health`

### Test with `curl`:
```bash
curl -X POST "${SERVICE_URL}/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "Where is my order #19028? Can you tell me when it arrives?"}'
```

---

## 🛠️ Deploying to Your Own GCP Project

```bash
# 1. Authenticate gcloud and set your project
gcloud config set project YOUR_PROJECT_ID

# 2. Store your TypeSafe API key in Secret Manager
echo -n "YOUR_TYPESAFE_API_KEY" | gcloud secrets create typesafe-api-key \
  --replication-policy="automatic" \
  --data-file=-

# 3. Deploy directly from source
./deploy.sh YOUR_PROJECT_ID us-central1
```

See **[RESULTS.md](RESULTS.md)** for test outputs across different inquiry categories.
