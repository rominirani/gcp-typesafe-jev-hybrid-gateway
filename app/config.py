"""Application Configuration Management via Pydantic Settings."""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Google Cloud Gemini Enterprise Agent Platform Config
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    google_cloud_location: str = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    # TypeSafe Jev Config (No fallbacks - requires real API key)
    typesafe_api_key: str = os.getenv("TYPESAFE_API_KEY", "")
    typesafe_api_url: str = os.getenv("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
    typesafe_model: str = os.getenv("TYPESAFE_MODEL", "jev-latest")

    # Routing Thresholds
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.90"))

    # BigQuery Telemetry Sink
    enable_bigquery_telemetry: bool = os.getenv("ENABLE_BIGQUERY_TELEMETRY", "false").lower() in ("true", "1", "yes")
    bigquery_dataset: str = os.getenv("BIGQUERY_DATASET", "ai_gateway_telemetry")
    bigquery_table: str = os.getenv("BIGQUERY_TABLE", "gateway_metrics")

    # Server Config
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8080"))

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
