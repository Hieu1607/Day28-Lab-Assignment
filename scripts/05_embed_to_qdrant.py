import os

from platform_lib import load_delta_records, load_local_env, upsert_records_to_qdrant

def embed_and_store(records: list[dict]):
    load_local_env()
    embed_url = os.getenv("EMBED_NGROK_URL", "").strip() or None
    stored = upsert_records_to_qdrant(records, embed_url=embed_url)
    print(f"Integration 5 OK: {stored} vectors stored in Qdrant")

records = load_delta_records()
if not records:
    records = [
        {"id": "doc_001", "text": "AI platform integration test"},
        {"id": "doc_002", "text": "Kafka to Prefect pipeline"},
    ]

embed_and_store(records)
