# Alert và runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1 — High latency P95

- Tên: `high_latency_p95`
- Severity: warning
- Duration: 10 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: `fast_successful_requests`, latency ≤ 3000 ms.
- Điều kiện và thời gian duy trì: P95 `response_sent.latency_ms` > 3000 ms trong 10 phút.
- Ảnh hưởng tới người dùng: phản hồi chậm, timeout hoặc trải nghiệm chat suy giảm.
- Ba bước kiểm tra đầu tiên: xem panel latency/TTFT; lọc log theo khoảng thời gian; mở trace và so sánh retrieval với generation.
- Mitigation tạm thời: giảm concurrency, tắt workload nặng và bật fallback/local prompt nếu Langfuse hoặc upstream chậm.
- Owner: `platform-oncall`

## Alert 2 — Retrieval success degraded

- Tên: `retrieval_success_degraded`
- Severity: critical
- Duration: 5 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: retrieval success rate tối thiểu 90%.
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90` trong 5 phút.
- Ảnh hưởng tới người dùng: câu trả lời thiếu context hoặc request bị lỗi do retrieval.
- Ba bước kiểm tra đầu tiên: xem panel errors/retrieval; lọc `request_failed` và `tool_success=false`; mở trace có span retrieval lỗi.
- Mitigation tạm thời: chuyển sang fallback answer, retry có giới hạn và giảm traffic vào vector store.
- Owner: `llm-platform`

## Alert 3 — Daily LLM cost breach

- Tên: `daily_llm_cost_breach`
- Severity: warning
- Duration: 15 phút liên tục
- Kênh thông báo: Slack
- SLI/SLO liên quan: daily cost tối đa 2.5 USD.
- Điều kiện và thời gian duy trì: tổng `response_sent.cost_usd` trong 24 giờ > 2.5 USD trong 15 phút.
- Ảnh hưởng tới người dùng: chi phí vận hành vượt ngân sách, có thể dẫn tới throttling.
- Ba bước kiểm tra đầu tiên: xem panel cost; phân tích tokens/model; mở trace có output token bất thường.
- Mitigation tạm thời: giới hạn output tokens, giảm concurrency và chuyển traffic sang model/cấu hình tiết kiệm hơn.
- Owner: `finops-oncall`
