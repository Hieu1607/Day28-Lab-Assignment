# Lab #28 — Full Platform Integration Sprint

AI platform hybrid cho Lab 28, đã được chỉnh lại để chạy được ổn định trên local bằng Docker Compose và một môi trường `conda` riêng. Repo hỗ trợ 2 chế độ:

- `mock/local`: không cần Kaggle hay LangSmith key, dùng để pass smoke tests và demo local end-to-end.
- `remote/hybrid`: gắn `VLLM_NGROK_URL`, `EMBED_NGROK_URL`, `LANGCHAIN_API_KEY` để nối sang Kaggle + LangSmith thật.

## Trạng thái đã verify

- `docker compose ps`: toàn bộ services `Up`
- Kafka ingest hoạt động
- Kafka → Delta Lake ghi parquet thành công
- Delta Lake → Redis hoạt động
- Delta Lake/sample → Qdrant hoạt động
- API Gateway trả lời được ở chế độ `mock`
- Prometheus scrape được API Gateway
- Prefect server + worker chạy được
- Prefect deployment `Kafka to Delta Pipeline/kafka-to-delta` đã được đăng ký trên server
- `pytest smoke-tests/ -v`: `9 passed`
- `python scripts/production_readiness_check.py`: `10/10 = 100%`

## 1. Tạo môi trường conda

```bash
conda env create -f environment.yml
conda activate day28-lab
```

Nếu đã có env rồi:

```bash
conda activate day28-lab
```

## 2. Cấu hình environment variables

```bash
cp .env.example .env
```

Mặc định `.env.example` đang để `LLM_MODE=mock`, nên local stack có thể chạy ngay mà không cần Kaggle.

Để dùng hybrid thật, điền thêm:

```env
VLLM_NGROK_URL=https://...
EMBED_NGROK_URL=https://...
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=lab28-platform
LLM_MODE=auto
```

## 3. Khởi động stack local

```bash
docker compose up -d --build
docker compose ps
```

Endpoints:

- Prefect UI: http://localhost:4200
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090
- Qdrant: http://localhost:6333/dashboard
- API Gateway: http://localhost:8000

## 4. Chạy data pipeline

### 4.1 Ingest vào Kafka

```bash
python scripts/01_ingest_to_kafka.py
```

### 4.2 Materialize Kafka → Delta Lake

Chạy local một lần:

```bash
python prefect/flows/kafka_to_delta.py
```

Đăng ký deployment Prefect và serve schedule:

```bash
set PREFECT_API_URL=http://localhost:4200/api
set PREFECT_SERVE=1
python prefect/flows/kafka_to_delta.py
```

Deployment sẽ xuất hiện trên Prefect UI với tên:

```text
Kafka to Delta Pipeline/kafka-to-delta
```

### 4.3 Delta Lake → Redis

```bash
python scripts/03_delta_to_feast.py
```

### 4.4 Embed vào Qdrant

```bash
python scripts/05_embed_to_qdrant.py
```

Nếu `EMBED_NGROK_URL` trống, script sẽ dùng embedding local deterministic để giữ pipeline testable.

## 5. Kiểm tra API

### Health

```bash
curl http://localhost:8000/health
```

### Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"What is platform engineering?\",\"embedding\":[0.1,0.1,0.1]}"
```

Trong `mock/local`, API vẫn trả lời được để smoke test không phụ thuộc Kaggle.

## 6. Observability

Kiểm tra metrics và traces:

```bash
python scripts/09_verify_observability.py
```

Hành vi hiện tại:

- Prometheus: bắt buộc pass
- LangSmith: `SKIPPED` nếu chưa cấu hình `LANGCHAIN_API_KEY`

## 7. Smoke Tests

```bash
pytest smoke-tests/ -v
```

Kết quả đã verify trong môi trường này:

```text
9 passed
```

## 8. Production Readiness

```bash
python scripts/production_readiness_check.py
```

Kết quả đã verify trong môi trường này:

```text
Production Readiness Score: 10/10 = 100%
```

## Cấu trúc chính

- `docker-compose.yml`: local stack
- `api-gateway/main.py`: FastAPI gateway, Prometheus metrics, mock fallback
- `prefect/flows/kafka_to_delta.py`: flow Prefect + local one-shot mode + serve mode
- `scripts/platform_lib.py`: helpers dùng chung cho Kafka, Delta Lake, Redis, Qdrant
- `smoke-tests/test_e2e.py`: smoke tests end-to-end

## Các thay đổi kỹ thuật quan trọng

- Sửa `prefect orion` cũ sang `prefect server start`
- Worker Prefect tự chờ server rồi tạo `lab28-pool`
- Sửa xung đột dependency `fastapi` và `prometheus-fastapi-instrumentator`
- Khóa `numpy<2` và `griffe<1` để tránh lỗi runtime với `pandas/pyarrow` và `prefect 2.14`
- API Gateway có fallback `mock` khi chưa có `VLLM_NGROK_URL`
- Script embedding có fallback local khi chưa có `EMBED_NGROK_URL`
- Readiness check không còn phụ thuộc tên container cứng

## Những gì còn cần hoàn thiện thủ công cho submission cuối

- Chụp screenshots thật vào thư mục `screenshots/`
- Nếu muốn demo hybrid đúng yêu cầu gốc, cần cung cấp Kaggle GPU notebook + tunnel URLs
- Nếu muốn verify LangSmith thật, cần cấu hình `LANGCHAIN_API_KEY`
- Nếu cần nộp demo video/live demo, phải rehearse với session Kaggle đang còn active

## Lệnh dọn dẹp

```bash
docker compose down
```
