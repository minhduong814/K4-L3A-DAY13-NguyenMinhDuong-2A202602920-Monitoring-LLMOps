"""Extract CP3 metric/log evidence without exposing challenge queries or seed."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.challenge import load_challenge


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def percentile(values: list[float], p: int) -> float:
    values = sorted(values)
    if not values:
        return 0.0
    index = min(len(values) - 1, max(0, round((p / 100) * len(values) + 0.5) - 1))
    return values[index]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", type=Path, default=Path("data/logs.jsonl"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    challenge = load_challenge()
    records = []
    for line in args.logs.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("ts"):
            records.append(record)

    enabled = [r for r in records if r.get("event") == "incident_enabled"]
    if not enabled:
        raise SystemExit("Chưa có incident_enabled trong log; hãy chạy challenge trước.")
    start = parse_time(enabled[-1]["ts"])
    window = [r for r in records if parse_time(r["ts"]) >= start]
    responses = [
        r for r in window
        if r.get("event") == "response_sent" and r.get("feature") == challenge.affected_feature
    ]
    latencies = [float(r["latency_ms"]) for r in responses if r.get("latency_ms") is not None]
    abnormal = [r for r in responses if float(r.get("latency_ms", 0)) > challenge.latency_threshold_ms]
    if not responses:
        raise SystemExit("Không tìm thấy response của challenge trong log.")

    lines = [
        "CP3 incident evidence (challenge-safe extract)",
        f"Challenge ID: {challenge.challenge_id}",
        f"Incident: {challenge.incident}",
        f"Affected feature: {challenge.affected_feature}",
        f"Investigation window: {window[0]['ts']} to {window[-1]['ts']}",
        f"Latency threshold: {challenge.latency_threshold_ms} ms",
        f"Requests analyzed: {len(responses)}",
        f"Latency P95: {percentile(latencies, 95):.0f} ms",
        f"Latency max: {max(latencies):.0f} ms",
        f"Abnormal requests: {len(abnormal)}",
        "",
        "Abnormal log correlations:",
    ]
    for record in abnormal:
        lines.append(
            json.dumps(
                {
                    "ts": record.get("ts"),
                    "event": record.get("event"),
                    "correlation_id": record.get("correlation_id"),
                    "feature": record.get("feature"),
                    "latency_ms": record.get("latency_ms"),
                    "ttft_ms": record.get("ttft_ms"),
                    "tool_name": record.get("tool_name"),
                    "tool_success": record.get("tool_success"),
                },
                ensure_ascii=False,
            )
        )
    output = "\n".join(lines) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Đã lưu: {args.output}")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
