"""Render a dependency-free runtime dashboard from the structured JSONL log."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from statistics import mean


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    index = min(len(values) - 1, max(0, round((p / 100) * len(values) + 0.5) - 1))
    return values[index]


def load_records(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Không tìm thấy {path}; hãy chạy API và load test trước.")
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    if not records:
        raise SystemExit(f"Không có structured log hợp lệ trong {path}.")
    return records


def panel(title: str, unit: str, threshold: str, body: str) -> str:
    return f"""<section class='panel'><h2>{html.escape(title)}</h2>
<div class='meta'>Unit: {html.escape(unit)} · Threshold/SLO: {html.escape(threshold)}</div>
<div class='value'>{body}</div></section>"""


def render(records: list[dict]) -> str:
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    latencies = [float(r["latency_ms"]) for r in responses if "latency_ms" in r]
    ttft = [float(r["ttft_ms"]) for r in responses if "ttft_ms" in r]
    costs = [float(r["cost_usd"]) for r in responses if "cost_usd" in r]
    tokens_in = sum(int(r.get("tokens_in", 0)) for r in responses)
    tokens_out = sum(int(r.get("tokens_out", 0)) for r in responses)
    quality = [float(r["quality_score"]) for r in responses if "quality_score" in r]
    retrieval = [r.get("tool_success") for r in responses if "tool_success" in r]
    retrieval_rate = (sum(x is True for x in retrieval) / len(retrieval) * 100) if retrieval else 0
    error_rate = len(failures) / len(requests) * 100 if requests else 0
    rate = len(requests) / 60

    cards = [
        panel(
            "Latency percentiles and TTFT",
            "ms",
            "P95 ≤ 3000 ms",
            f"P50 {percentile(latencies, 50):.0f} · P95 {percentile(latencies, 95):.0f} · P99 {percentile(latencies, 99):.0f}<br>TTFT P95 {percentile(ttft, 95):.0f}",
        ),
        panel("Request traffic", "requests_per_minute", "≥ 1 request/min", f"{len(requests)} requests<br>{rate:.2f} requests/min"),
        panel("Error rate and retrieval success", "percent", "Error ≤ 2% · Retrieval ≥ 90%", f"Errors {error_rate:.2f}%<br>Retrieval success {retrieval_rate:.2f}%"),
        panel("Cost over time", "usd", "Total ≤ 2.5 USD", f"Total ${sum(costs):.6f}<br>Average ${mean(costs) if costs else 0:.6f}"),
        panel("Input and output tokens", "tokens", "Total ≤ 50000", f"Input {tokens_in:,}<br>Output {tokens_out:,}"),
        panel("Quality proxy", "score_0_to_1", "Mean ≥ 0.75", f"Mean {mean(quality) if quality else 0:.3f}"),
    ]
    return """<!doctype html><html lang='en'><head><meta charset='utf-8'>
<title>K4-L3A Day 13 Monitoring Dashboard</title><style>
body{font-family:Arial,sans-serif;background:#f5f7fb;color:#172033;margin:32px}
h1{margin-bottom:4px}.sub{color:#526070;margin-bottom:24px}.grid{display:grid;grid-template-columns:repeat(2,minmax(320px,1fr));gap:16px}
.panel{background:#fff;border:1px solid #d9e0ea;border-radius:10px;padding:18px;min-height:130px;box-shadow:0 2px 8px #17203312}
h2{font-size:18px;margin:0 0 12px}.meta{font-size:12px;color:#526070;margin-bottom:18px}.value{font-size:20px;line-height:1.7;font-weight:600}
</style></head><body><h1>K4-L3A Day 13 Monitoring &amp; LLMOps</h1>
<div class='sub'>Runtime dashboard · time range: last 60 minutes · refresh: 30 seconds · source: data/logs.jsonl</div>
<div class='grid'>""" + "".join(cards) + "</div></body></html>"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/logs.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("submission/evidence/dashboard-runtime.html"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(load_records(args.input)), encoding="utf-8")
    print(f"Dashboard đã tạo: {args.output}")


if __name__ == "__main__":
    main()
