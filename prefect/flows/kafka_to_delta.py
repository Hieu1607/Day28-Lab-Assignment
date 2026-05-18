from __future__ import annotations

import os
import sys
from pathlib import Path

from prefect import flow, task

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.platform_lib import consume_kafka_records, save_records_to_delta

@task
def consume_and_process(bootstrap_servers: str = "localhost:9092"):
    records = consume_kafka_records(bootstrap_servers=bootstrap_servers)
    print(f"Consumed {len(records)} records from Kafka")
    return records

@task
def save_to_delta(records, delta_dir: str):
    if not records:
        print("No records to save")
        return

    output_path = save_records_to_delta(records, delta_dir=delta_dir)
    if output_path:
        print(f"Saved {len(records)} records to Delta Lake at {output_path}")


@flow(name="Kafka to Delta Pipeline", log_prints=True)
def kafka_to_delta_flow(
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    delta_dir: str = os.getenv("DELTA_LAKE_DIR", str(ROOT_DIR / "delta-lake" / "raw")),
):
    records = consume_and_process(bootstrap_servers=bootstrap_servers)
    save_to_delta(records, delta_dir=delta_dir)


def run_once_local(
    bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    delta_dir: str = os.getenv("DELTA_LAKE_DIR", str(ROOT_DIR / "delta-lake" / "raw")),
) -> None:
    records = consume_kafka_records(bootstrap_servers=bootstrap_servers)
    print(f"Consumed {len(records)} records from Kafka")
    output_path = save_records_to_delta(records, delta_dir=delta_dir)
    if output_path:
        print(f"Saved {len(records)} records to Delta Lake at {output_path}")
    else:
        print("No records to save")


def deploy_flow() -> None:
    deploy_kwargs = {
        "name": "kafka-to-delta",
        "work_pool_name": os.getenv("PREFECT_WORK_POOL", "lab28-pool"),
    }
    deployment_image = os.getenv("PREFECT_DEPLOYMENT_IMAGE")
    if deployment_image:
        deploy_kwargs["image"] = deployment_image

    kafka_to_delta_flow.deploy(**deploy_kwargs)


def serve_flow() -> None:
    kafka_to_delta_flow.serve(
        name="kafka-to-delta",
        cron="*/5 * * * *",
        pause_on_shutdown=False,
    )


if __name__ == "__main__":
    if os.getenv("PREFECT_DEPLOY", "0") == "1":
        deploy_flow()
    elif os.getenv("PREFECT_SERVE", "0") == "1":
        serve_flow()
    else:
        run_once_local()
