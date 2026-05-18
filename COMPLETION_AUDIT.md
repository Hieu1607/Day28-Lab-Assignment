# Completion Audit

## Objective restated as deliverables

1. Hoàn thiện toàn bộ local platform stack của assignment.
2. Dùng môi trường `conda` mới, tránh dependency hỏng mặc định.
3. Chạy được các integration points cốt lõi và Prefect deployment.
4. Chạy smoke tests và production readiness check với bằng chứng thật.
5. Chuẩn bị đầy đủ artifacts nộp bài khả thi trong repo.
6. Commit và push lên `main` của `Hieu1607/Day28-Lab-Assignment`.
7. Nêu rõ phần nào đã làm xong và phần nào còn phụ thuộc external secrets/hạ tầng.

## Checklist mapped to evidence

| Requirement | Evidence |
|---|---|
| Conda env mới | [environment.yml](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/environment.yml) |
| Docker stack chạy | `docker compose ps` đã xác minh mọi service `Up` |
| Ingest Kafka | [scripts/01_ingest_to_kafka.py](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/scripts/01_ingest_to_kafka.py) và log chạy thành công |
| Kafka → Delta | [prefect/flows/kafka_to_delta.py](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/prefect/flows/kafka_to_delta.py) và parquet được materialize khi chạy |
| Delta → Redis | [scripts/03_delta_to_feast.py](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/scripts/03_delta_to_feast.py) |
| Embedding/Qdrant | [scripts/05_embed_to_qdrant.py](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/scripts/05_embed_to_qdrant.py) |
| API Gateway | [api-gateway/main.py](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/api-gateway/main.py) và screenshot [api_gateway.png](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/screenshots/api_gateway.png) |
| Prefect deployment | `prefect deployment ls` cho thấy `Kafka to Delta Pipeline/kafka-to-delta` |
| Smoke tests | [smoke_tests_results.txt](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/smoke_tests_results.txt) và [smoke_tests_results.png](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/smoke_tests_results.png) |
| Production readiness >80% | [production_readiness.txt](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/production_readiness.txt) và [production_readiness.png](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/production_readiness.png) |
| Submission screenshots | [prefect_ui.png](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/screenshots/prefect_ui.png), [api_gateway.png](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/screenshots/api_gateway.png), [grafana_dashboard.png](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/screenshots/grafana_dashboard.png) |
| Submission Q&A | [SUBMISSION_ANSWERS.md](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/SUBMISSION_ANSWERS.md) |
| Status summary | [DELIVERABLE_STATUS.md](/C:/Users/Admin/Desktop/Day28-Lab-Assignment/DELIVERABLE_STATUS.md) |
| Push lên repo Hieu1607 | `origin` trỏ tới `https://github.com/Hieu1607/Day28-Lab-Assignment.git` và commit đã push lên `main` |

## Remaining gaps

- Không thể verify LangSmith trace thật nếu không có `LANGCHAIN_API_KEY`.
- Không thể verify hybrid Kaggle serving thật nếu không có GPU notebook/tunnel URL đang hoạt động.
- Live demo rehearsal cuối cùng vẫn là thao tác thủ công bên người nộp.

Các gap trên đều phụ thuộc external secret hoặc external infra, không phải thiếu sót còn tiếp tục sửa được chỉ trong repo này.
