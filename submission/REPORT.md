# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Minh Dương
- **MSSV:** 2A202602920
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/minhduong814/K4-L3A-DAY13-NguyenMinhDuong-2A202602920-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602920`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10a-production-v2.png`, `evidence/10b-rollback-v1.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Chưa ghi | 100/100 | CP1: đủ schema, correlation ID, enrichment và không phát hiện PII |
| `validate_dashboard.py` | Chưa ghi | 6/6 panel | Contract dashboard hợp lệ |
| `pytest` | Chưa ghi | 22 passed | CP1/CP2 tests pass |
| Số traces hợp lệ | Chưa ghi | 20 root traces | Langfuse evidence hiển thị 20 root traces cá nhân |
| Số PII leak | Chưa ghi | 0 | Validator độc lập không phát hiện PII |
| Latency P95 / TTFT P95 | Chưa ghi | 874 ms / 50 ms | Theo dashboard runtime evidence |
| Retrieval success rate | Chưa ghi | 100% | Theo dashboard runtime evidence |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id` nếu đúng format `req-<8-hex>`, ngược lại sinh ID mới; bind vào structlog context và trả lại qua response header/API response.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`, cùng latency/TTFT/token/cost ở response log.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước `JsonlFileProcessor` và JSON renderer, đệ quy qua toàn bộ event; email, điện thoại VN, CCCD và thẻ được thay bằng placeholder.
- **Cách kiểm chứng kết quả:** `python -m pytest -q` đạt 22 passed và `python scripts/validate_logs.py` đạt 100/100 trên log mới; xem `evidence/02-log-validator.png`, `04-structured-log.png`, `05-pii-redaction.png`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Mở project `day13-k4-l3a-2A202602920` và lọc time range sau workload cá nhân; trace metadata có user hash, session và correlation ID của log local.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` là root; `retrieval` là child `retriever`; `llm-generation` là child `generation` có model, prompt, usage và cost.
- **Cách nối trace với log:** Dùng cùng `correlation_id` trong structured log và trace metadata.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** v1 với `baseline`, `production`.
- **Version/label candidate:** v2 với `candidate`.
- **Trace ID của mỗi version:** `95b752470a1afa09173af86ea2777bbd`; `ac40e15992a6918e61ab5dca8ae07b85`
- **Cách promote và rollback `production`:** Chuyển label `production` từ v1 sang v2, chạy trace kiểm chứng, sau đó chuyển lại v1 và chạy trace kiểm chứng lần hai.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** `config/dashboard.yaml`, gồm latency/TTFT, traffic, errors/retrieval, cost, tokens và quality; runtime evidence tại `evidence/11-dashboard-overview.png`.
- **SLO và lý do chọn:** `fast_successful_requests`, 99.5% trong 28 ngày, với latency thành công không quá 3000 ms.
- **Cách tính error budget:** `100% - 99.5% = 0.5%` tổng request trong cửa sổ 28 ngày.
- **Ba alert và runbook tương ứng:** `high_latency_p95`, `retrieval_success_degraded`, `daily_llm_cost_breach`; cấu hình ở `config/alert_rules.yaml`, hướng dẫn ở `docs/alerts.md`.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-10-01T09:55:46Z` – `2026-10-01T09:56:01Z` UTC.
- **Triệu chứng từ metrics:** Feature `monitoring` có 5/5 response vượt ngưỡng 2000 ms; latency P95 và max là khoảng 3434 ms.
- **Log line và correlation ID liên quan:** `response_sent`, `latency_ms=3434`, `tool_name=retrieval`, `tool_success=true`; dùng một trong các ID ở `evidence/13-incident-log.png`.
- **Trace ID và span gây ảnh hưởng:** Cần thay bằng trace mới tương ứng với correlation ID trong evidence 13; span gây ảnh hưởng là `retrieval`.
- **Root cause:** Incident `rag_slow` làm bước retrieval chậm khoảng 2.5 giây, kéo latency toàn request vượt threshold; generation/TTFT vẫn khoảng 50 ms.
- **Fix action:** Đã disable incident `rag_slow`; xác nhận lại trạng thái incident false và chạy workload kiểm chứng.
- **Preventive measure:** Alert P95 latency > 3000 ms trong 10 phút, theo dõi retrieval span riêng và liên kết dashboard → log → trace bằng correlation ID.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
