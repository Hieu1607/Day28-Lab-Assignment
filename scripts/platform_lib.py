from __future__ import annotations

import glob
import hashlib
import json
import os
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import redis
from dotenv import load_dotenv
from kafka import KafkaConsumer, KafkaProducer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DELTA_DIR = ROOT_DIR / "delta-lake" / "raw"
DEFAULT_VECTOR_SIZE = 384


def load_local_env() -> None:
    load_dotenv(ROOT_DIR / ".env")


def ingest_records(records: list[dict], bootstrap_servers: str = "localhost:9092") -> None:
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )
    for record in records:
        producer.send("data.raw", value=record)
        print(f"Sent: {record['id']}")
    producer.flush()
    producer.close()


def consume_kafka_records(
    bootstrap_servers: str,
    topic: str = "data.raw",
    consumer_timeout_ms: int = 5000,
) -> list[dict]:
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        consumer_timeout_ms=consumer_timeout_ms,
        value_deserializer=lambda msg: json.loads(msg.decode("utf-8")),
    )
    records = [message.value for message in consumer]
    consumer.close()
    return records


def save_records_to_delta(records: list[dict], delta_dir: str | os.PathLike[str] = DEFAULT_DELTA_DIR) -> Path | None:
    if not records:
        return None

    target_dir = Path(delta_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    pd.DataFrame(records).to_parquet(output_path)
    return output_path


def load_delta_records(delta_dir: str | os.PathLike[str] = DEFAULT_DELTA_DIR) -> list[dict]:
    files = sorted(glob.glob(str(Path(delta_dir) / "*.parquet")))
    if not files:
        return []

    frame = pd.concat([pd.read_parquet(file_path) for file_path in files], ignore_index=True)
    return frame.to_dict(orient="records")


def push_features_to_redis(
    records: list[dict],
    host: str = "localhost",
    port: int = 6379,
) -> int:
    client = redis.Redis(host=host, port=port, decode_responses=True)
    for record in records:
        feature_key = f"feature:{record['id']}"
        client.set(
            feature_key,
            json.dumps(
                {
                    "text": record["text"],
                    "timestamp": record.get("timestamp"),
                    "processed": True,
                }
            ),
        )
    return len(records)


def _local_embedding(text: str, vector_size: int = DEFAULT_VECTOR_SIZE) -> list[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    return [round(rng.uniform(-1.0, 1.0), 6) for _ in range(vector_size)]


def embed_texts(
    texts: list[str],
    embed_url: str | None = None,
    vector_size: int = DEFAULT_VECTOR_SIZE,
) -> list[list[float]]:
    if embed_url:
        response = requests.post(
            f"{embed_url.rstrip('/')}/embed",
            json={"texts": texts},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["embeddings"]

    return [_local_embedding(text, vector_size=vector_size) for text in texts]


def ensure_qdrant_collection(
    client: QdrantClient,
    collection_name: str = "documents",
    vector_size: int = DEFAULT_VECTOR_SIZE,
) -> None:
    collections = {collection.name for collection in client.get_collections().collections}
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_records_to_qdrant(
    records: list[dict],
    host: str = "localhost",
    port: int = 6333,
    collection_name: str = "documents",
    embed_url: str | None = None,
    vector_size: int = DEFAULT_VECTOR_SIZE,
) -> int:
    client = QdrantClient(host=host, port=port)
    ensure_qdrant_collection(client, collection_name=collection_name, vector_size=vector_size)
    embeddings = embed_texts([record["text"] for record in records], embed_url=embed_url, vector_size=vector_size)
    points = [
        PointStruct(
            id=abs(hash(str(record["id"]))) % (2**31 - 1),
            vector=embedding,
            payload=record,
        )
        for record, embedding in zip(records, embeddings)
    ]
    client.upsert(collection_name=collection_name, points=points)
    return len(points)
