# Submission Answers

## 1. Trade-offs giữa performance, reliability, maintainability

Thiết kế hiện tại ưu tiên maintainability và reliability trước performance tuyệt đối. Kafka được dùng để tách producer khỏi downstream processing, giúp replay dữ liệu và giảm coupling. API Gateway có fallback `mock` để local platform vẫn test được khi remote serving unavailable. Đổi lại, đường đi request dài hơn và có thêm overhead từ Kafka, Qdrant, Redis, Prometheus, nhưng cấu trúc này dễ kiểm soát và dễ mở rộng hơn một kiến trúc gọi trực tiếp.

## 2. Xử lý ngắt kết nối giữa local và Kaggle

Repo hiện hỗ trợ 2 chế độ. Khi có `VLLM_NGROK_URL` và `EMBED_NGROK_URL`, gateway và embedding script gọi remote services thật. Khi kết nối Kaggle mất hoặc URL chưa được cấu hình, gateway tự fallback sang `mock-local` và script embedding dùng deterministic local embeddings. Điều này không thay thế inference thật, nhưng giữ cho smoke test, observability và phần lớn local integration vẫn hoạt động.

## 3. Kafka giúp decouple components như thế nào

Kafka tách ingestion khỏi processing. Producer chỉ cần ghi vào topic `data.raw`, còn bước materialization sang Delta Lake, Redis hoặc Qdrant có thể chạy riêng, retry riêng, và scale riêng. Cách này giúp replay dữ liệu khi flow lỗi, giảm phụ thuộc thời gian thực giữa các service, và thuận lợi hơn cho debugging lẫn observability.

## 4. Observability được implement ra sao

API Gateway expose `/metrics` qua `prometheus-fastapi-instrumentator`, Prometheus scrape endpoint này định kỳ, Grafana đọc dữ liệu từ Prometheus để hiển thị dashboard, và script `09_verify_observability.py` kiểm tra trực tiếp việc metrics đã đi qua đường này hay chưa. LangSmith vẫn được giữ như integration point tùy chọn; nếu có `LANGCHAIN_API_KEY`, repo có thể xác minh trace thật, còn nếu không thì script báo `SKIPPED` thay vì fail mơ hồ.

## 5. Nếu một service như Qdrant hoặc Kafka bị crash thì sao

Hệ thống hiện có graceful degradation ở một số điểm. Nếu Qdrant lỗi hoặc collection chưa sẵn sàng, API Gateway không crash toàn bộ mà trả lời với context rỗng hoặc fallback `mock`. Nếu Kaggle serving mất, gateway chuyển sang `mock` thay vì hard fail. Với Kafka, dữ liệu được giữ ở topic nên có thể replay sau khi consumer/flow hồi phục. Tuy vậy, repo này chưa triển khai circuit breaker đầy đủ hay retry policy nhiều tầng; đó là phần mở rộng phù hợp cho production hardening tiếp theo.
