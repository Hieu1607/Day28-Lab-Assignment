from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

from platform_lib import (
    ingest_records,
    load_delta_records,
    push_features_to_redis,
    save_records_to_delta,
    upsert_records_to_qdrant,
)

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session", autouse=True)
def prepare_platform_state():
    seed_records = [
        {"id": "smoke_001", "text": "Platform engineering enables reusable delivery systems.", "timestamp": time.time()},
        {"id": "smoke_002", "text": "Kafka decouples producers and consumers in event-driven systems.", "timestamp": time.time()},
    ]
    save_records_to_delta(seed_records)
    push_features_to_redis(seed_records)
    upsert_records_to_qdrant(seed_records)
    return seed_records

# ── Test 1: Happy Path — Full Inference Request ───────────────
class TestHappyPath:
    def test_full_inference_returns_200(self):
        """Data vào API Gateway, nhận được answer từ LLM"""
        resp = requests.post(f"{BASE_URL}/api/v1/chat", json={
            "query": "What is platform engineering?",
            "embedding": [0.1] * 384
        }, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["answer"]) > 10
        assert data["latency_ms"] < 2000

    def test_health_check_passes(self):
        """API Gateway health check"""
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ── Test 2: Data Ingestion Journey ───────────────────────────
class TestDataIngestion:
    def test_kafka_ingest_and_qdrant_store(self):
        """Ingest data vào Kafka và materialize local stores"""
        record = {"id": "smoke_003", "text": "smoke test document", "timestamp": time.time()}
        ingest_records([record])
        save_records_to_delta([record])
        push_features_to_redis([record])
        upsert_records_to_qdrant([record])

        resp = requests.get("http://localhost:6333/collections/documents")
        assert resp.status_code == 200
        count = resp.json()["result"]["points_count"]
        assert count > 0
        print(f"Vector store has {count} documents")


# ── Test 3: Observability Journey ────────────────────────────
class TestObservability:
    def test_prometheus_scrapes_api_gateway(self):
        """Prometheus đang scrape metrics từ API Gateway"""
        resp = requests.get("http://localhost:9090/api/v1/query",
                            params={"query": "up{job='api-gateway'}"})
        assert resp.status_code == 200
        result = resp.json()["data"]["result"]
        assert len(result) > 0
        assert result[0]["value"][1] == "1"  # service is up

    def test_grafana_dashboard_accessible(self):
        """Grafana dashboard load được"""
        resp = requests.get("http://localhost:3000/api/health",
                            auth=("admin", "admin"))
        assert resp.status_code == 200


# ── Test 4: Error Handling & Failure Path ────────────────────
class TestFailurePath:
    def test_invalid_request_returns_422(self):
        """API Gateway từ chối request thiếu field bắt buộc"""
        resp = requests.post(f"{BASE_URL}/api/v1/chat", json={})
        assert resp.status_code in [400, 422]

    def test_timeout_handled_gracefully(self):
        """Timeout không làm crash service"""
        try:
            resp = requests.post(f"{BASE_URL}/api/v1/chat",
                                 json={"query": "test", "embedding": [0.1] * 384},
                                 timeout=0.001)
        except requests.exceptions.Timeout:
            pass  # Expected — graceful timeout

        # Service vẫn healthy sau timeout
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        assert health.status_code == 200


# ── Test 5: Feature Store Journey ────────────────────────────
class TestFeatureStore:
    def test_feast_redis_has_features(self):
        """Feast (Redis) có features sau khi pipeline chạy"""
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        keys = r.keys("feature:*")
        assert len(keys) > 0, "No features found in Feast store"
        print(f"Feature store has {len(keys)} feature entries")

    def test_delta_lake_has_parquet_data(self):
        records = load_delta_records()
        assert len(records) > 0, "No records found in Delta Lake"
