import argparse
import platform
import statistics
import time
import tomllib
from datetime import date
from pathlib import Path

from travel_companion.intent_router import route_transcript

DEFAULT_SAMPLES_PATH = Path("specimens/intent_samples.toml")
DEFAULT_RESULTS_PATH = Path("docs/results/T6-intent-router-latency.md")
REPETITIONS_PER_SAMPLE = 200
MICROSECONDS_PER_SECOND = 1_000_000


def load_intent_samples(samples_path: Path) -> list[dict]:
    return tomllib.loads(samples_path.read_text())["sample"]


def routing_microseconds(transcript: str) -> float:
    started = time.perf_counter()
    route_transcript(transcript)
    return (time.perf_counter() - started) * MICROSECONDS_PER_SECOND


def median_routing_microseconds(transcript: str) -> float:
    route_transcript(transcript)
    return statistics.median(routing_microseconds(transcript) for _ in range(REPETITIONS_PER_SAMPLE))


def routes_as_expected(sample: dict) -> bool:
    card = route_transcript(sample["transcript"])
    return card.intent == sample.get("intent") and card.details == sample.get("details", {})


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]


def sample_row(sample: dict, microseconds: float) -> str:
    intent = sample.get("intent", "unsupported (I can't do that yet)")
    verdict = "yes" if routes_as_expected(sample) else "NO"
    return f"| {sample['transcript']} | {intent} | {verdict} | {microseconds:.1f} |"


def latency_report(samples: list[dict], run_date: date) -> str:
    medians = [median_routing_microseconds(sample["transcript"]) for sample in samples]
    correct_count = sum(routes_as_expected(sample) for sample in samples)
    rows = "\n".join(sample_row(sample, microseconds) for sample, microseconds in zip(samples, medians))
    return f"""# T6: Intent router latency

Run on {run_date.isoformat()} with `.venv/bin/python -m travel_companion.intent_router_benchmark`.

## Machine

- {platform.machine()}, {platform.system()} {platform.release()}
- Python {platform.python_version()}

## Method

Each of the {len(samples)} sample transcripts in `specimens/intent_samples.toml` is routed {REPETITIONS_PER_SAMPLE} times in-process through `route_transcript` (the same call `POST /api/transcript` makes), after one warm-up call. The time per sample is the median of those runs. It covers the rules and building the answer card; HTTP and speech-to-text are not included. No model call is made on any sample.

## Summary

- Routed correctly: {correct_count} of {len(samples)}
- Median routing time: {statistics.median(medians):.1f} µs
- 95th percentile: {percentile(medians, 0.95):.1f} µs
- Slowest sample: {max(medians):.1f} µs

## Per sample

| Transcript | Expected intent | Routed correctly | Median, µs |
| --- | --- | --- | --- |
{rows}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure the rules-first intent router on the sample questions.")
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    arguments = parser.parse_args()
    report = latency_report(load_intent_samples(arguments.samples), date.today())
    arguments.results.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
