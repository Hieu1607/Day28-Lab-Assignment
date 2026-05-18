# Deliverable Status

## Hoàn thành và đã verify

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Docker Compose stack | Done | `docker compose ps` cho thấy tất cả services `Up` |
| Integration 1: Data → Kafka | Done | `python scripts/01_ingest_to_kafka.py` |
| Integration 2: Kafka → Delta Lake | Done | `python prefect/flows/kafka_to_delta.py` ghi parquet vào `delta-lake/raw/` |
| Integration 3+4: Delta Lake → Redis | Done | `python scripts/03_delta_to_feast.py` |
| Integration 5: Embedding → Qdrant | Done | `python scripts/05_embed_to_qdrant.py` |
| Integration 8: Serving → API Gateway | Done | `POST /api/v1/chat` trả về `200` |
| Integration 9: Prometheus | Done | `python scripts/09_verify_observability.py` báo `Integration 9 OK` |
| Prefect deployment | Done | Deployment `Kafka to Delta Pipeline/kafka-to-delta` xuất hiện trên Prefect server |
| Smoke tests | Done | [smoke_tests_results.txt](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/smoke_tests_results.txt) |
| Production readiness | Done | [production_readiness.txt](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/production_readiness.txt) |

## Còn lại hoặc không thể hoàn tất hoàn toàn trong môi trường này

| Hạng mục | Trạng thái | Lý do |
|---|---|---|
| Screenshots demo trong `screenshots/` | Manual | Repo đã tạo thư mục sẵn, nhưng chưa chụp file PNG thật từ phiên submit |
| LangSmith traces thực | Blocked by secret | Thiếu `LANGCHAIN_API_KEY` hợp lệ |
| Hybrid Kaggle serving thật | Blocked by external infra | Thiếu Kaggle GPU session đang chạy và tunnel URL thật |
| Live demo rehearsal | Manual | Cần người nộp tự chạy buổi demo với session thật |

## Commit đã push

- Branch: `main`
- Remote: `origin` → `https://github.com/Hieu1607/Day28-Lab-Assignment.git`
- Commit: `b39cff0`
