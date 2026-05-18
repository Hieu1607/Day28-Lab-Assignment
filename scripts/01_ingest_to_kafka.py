import time

from platform_lib import ingest_records, load_local_env


def ingest_data(records: list[dict]):
    load_local_env()
    ingest_records(records)

# Test
sample_data = [
    {"id": "doc_001", "text": "AI platform integration test", "timestamp": time.time()},
    {"id": "doc_002", "text": "Kafka to Prefect pipeline", "timestamp": time.time()},
]
ingest_data(sample_data)
print("Integration 1 OK: Data → Kafka")
