import argparse
import http.client
import json
import os
import platform
import re
import statistics
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from travel_companion.ask import ASK_SYSTEM_PROMPT
from travel_companion.chat_message import ChatMessage
from travel_companion.fact_guardrail import (
    PHRASE_FROM_FACTS_SYSTEM_PROMPT,
    adds_no_name,
    adds_no_number,
    facts_prompt,
    keeps_every_fact,
    phrased_answer,
)
from travel_companion.model_client import REQUEST_TIMEOUT_SECONDS, ModelClient, ModelUnavailable
from travel_companion.prompt_budget import REPLY_TOKENS, estimated_prompt_tokens, fit_to_prompt_budget
from travel_companion.rate import CurrentRate, rate_question

BENCHMARK_RATE_SOURCE = "benchmark"
SERVER_SENT_DATA_PREFIX = "data: "
SERVER_SENT_DONE = "[DONE]"
REPO_ROOT = Path(__file__).resolve().parents[2]
START_MODEL_SERVER_SCRIPT = REPO_ROOT / "scripts" / "start_model_server.sh"
DEFAULT_RESULTS_PATH = REPO_ROOT / "docs" / "results" / "T5-mac-model-benchmark.md"
DEFAULT_BENCHMARK_PORT = 8091
DEFAULT_SPEED_REPEATS = 5
DEFAULT_GUARDRAIL_REPEATS = 3
SERVER_START_TIMEOUT_SECONDS = 120.0
SERVER_STOP_TIMEOUT_SECONDS = 10.0
MEMORY_SAMPLE_INTERVAL_SECONDS = 0.1
KILOBYTES_PER_MEGABYTE = 1024
FOOTPRINT_PATTERN = re.compile(r"Footprint:\s*([\d.]+)\s*(KB|MB|GB)")
FOOTPRINT_UNIT_MEGABYTES = {"KB": 1 / 1024, "MB": 1.0, "GB": 1024.0}
STREAM_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, ValueError, http.client.HTTPException)
NO_REPLY_CELL = "no reply"
LONG_QUESTION = "Where can I buy a bus ticket in San José, and how early should I get to the station? " * 60


@dataclass(frozen=True)
class SpeedPrompt:
    name: str
    messages: list[ChatMessage]


@dataclass(frozen=True)
class StreamTiming:
    seconds_to_first_token: float
    tokens_per_second: float
    streamed_token_count: int


class EmptyStream(Exception):
    pass


@dataclass(frozen=True)
class SpeedResult:
    prompt: SpeedPrompt
    timings: list[StreamTiming]
    failed_stream_count: int = 0


@dataclass(frozen=True)
class GuardrailCase:
    rate: float
    question: str


@dataclass(frozen=True)
class GuardrailVerdict:
    case: GuardrailCase
    reply: str
    kept_every_fact: bool
    added_no_number: bool
    added_no_name: bool
    model_failed: bool = False

    @property
    def kept(self) -> bool:
        return self.kept_every_fact and self.added_no_number and self.added_no_name


@dataclass(frozen=True)
class BenchmarkResult:
    speed_results: list[SpeedResult]
    guardrail_verdicts: list[GuardrailVerdict]


@dataclass(frozen=True)
class MachineDescription:
    chip: str
    memory_gigabytes: int
    os_version: str
    llama_server_version: str
    model_file: str


@dataclass(frozen=True)
class MemoryReading:
    peak_resident_megabytes: float
    footprint_megabytes: float | None


def benchmark_rate(colones_per_dollar: float) -> CurrentRate:
    return CurrentRate(colones_per_dollar=colones_per_dollar, source=BENCHMARK_RATE_SOURCE)


def speed_prompts() -> list[SpeedPrompt]:
    rate_facts = rate_question("What is the rate?", benchmark_rate(510))
    return [
        SpeedPrompt(
            "short question (/api/ask)",
            [ChatMessage("system", ASK_SYSTEM_PROMPT), ChatMessage("user", "What does pura vida mean?")],
        ),
        SpeedPrompt(
            "phrase the Rate from facts (/api/ask/rate)",
            [ChatMessage("system", PHRASE_FROM_FACTS_SYSTEM_PROMPT), ChatMessage("user", facts_prompt(rate_facts))],
        ),
        SpeedPrompt(
            "long question trimmed to the prompt budget",
            fit_to_prompt_budget([ChatMessage("system", ASK_SYSTEM_PROMPT), ChatMessage("user", LONG_QUESTION)]),
        ),
    ]


RATE_QUESTIONS = (
    "What is the rate?",
    "How many colones do I get for one dollar?",
    "What's the exchange rate today?",
    "If I change one US dollar, how many colones is that?",
    "What is a dollar worth in Costa Rica?",
    "Tell me the colón to dollar rate.",
    "How much is 1 USD in CRC?",
    "Is the dollar strong against the colón right now?",
    "What rate should I expect when paying in dollars?",
    "Convert one dollar to colones for me.",
    "What's the rate for US dollars?",
    "How many ₡ per $?",
)
BENCHMARK_RATES = (510, 505.5, 498)


def fixed_guardrail_cases(repeats: int) -> list[GuardrailCase]:
    return [
        GuardrailCase(rate=rate, question=question)
        for _ in range(repeats)
        for rate in BENCHMARK_RATES
        for question in RATE_QUESTIONS
    ]


def streaming_request(endpoint_url: str, messages: list[ChatMessage]) -> urllib.request.Request:
    request_body = {
        "messages": [{"role": message.role, "content": message.content} for message in messages],
        "max_tokens": REPLY_TOKENS,
        "stream": True,
        "cache_prompt": False,
    }
    return urllib.request.Request(
        endpoint_url,
        data=json.dumps(request_body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )


def streamed_content(server_sent_line: bytes) -> str:
    line = server_sent_line.decode().strip()
    if not line.startswith(SERVER_SENT_DATA_PREFIX):
        return ""
    payload = line.removeprefix(SERVER_SENT_DATA_PREFIX)
    if payload == SERVER_SENT_DONE:
        return ""
    choices = json.loads(payload).get("choices") or [{}]
    return choices[0].get("delta", {}).get("content") or ""


def timed_stream(endpoint_url: str, messages: list[ChatMessage]) -> StreamTiming:
    content_arrival_times = []
    started_at = time.perf_counter()
    with urllib.request.urlopen(streaming_request(endpoint_url, messages), timeout=REQUEST_TIMEOUT_SECONDS) as stream:
        for server_sent_line in stream:
            if streamed_content(server_sent_line):
                content_arrival_times.append(time.perf_counter())
    if not content_arrival_times:
        raise EmptyStream("the stream had no content chunks")
    first_token_at, last_token_at = content_arrival_times[0], content_arrival_times[-1]
    decoding_seconds = last_token_at - first_token_at
    tokens_after_first = len(content_arrival_times) - 1
    return StreamTiming(
        seconds_to_first_token=first_token_at - started_at,
        tokens_per_second=tokens_after_first / decoding_seconds if decoding_seconds > 0 else 0.0,
        streamed_token_count=len(content_arrival_times),
    )


def timed_stream_or_none(endpoint_url: str, messages: list[ChatMessage]) -> StreamTiming | None:
    try:
        return timed_stream(endpoint_url, messages)
    except (EmptyStream, *STREAM_ERRORS):
        return None


def measured_speed(endpoint_url: str, prompt: SpeedPrompt, repeats: int) -> SpeedResult:
    attempts = [timed_stream_or_none(endpoint_url, prompt.messages) for _ in range(repeats)]
    timings = [timing for timing in attempts if timing is not None]
    return SpeedResult(prompt=prompt, timings=timings, failed_stream_count=len(attempts) - len(timings))


def failed_verdict(case: GuardrailCase) -> GuardrailVerdict:
    return GuardrailVerdict(
        case=case, reply="", kept_every_fact=False, added_no_number=False, added_no_name=False, model_failed=True
    )


def guardrail_verdict(case: GuardrailCase, model_client: ModelClient) -> GuardrailVerdict:
    factual_question = rate_question(case.question, benchmark_rate(case.rate))
    try:
        reply = phrased_answer(factual_question, model_client).strip()
    except ModelUnavailable:
        return failed_verdict(case)
    return GuardrailVerdict(
        case=case,
        reply=reply,
        kept_every_fact=keeps_every_fact(reply, factual_question.facts),
        added_no_number=adds_no_number(reply, factual_question),
        added_no_name=adds_no_name(reply, factual_question),
    )


def run_benchmark(endpoint_url: str, guardrail_cases: list[GuardrailCase], speed_repeats: int) -> BenchmarkResult:
    model_client = ModelClient(endpoint_url)
    return BenchmarkResult(
        speed_results=[measured_speed(endpoint_url, prompt, speed_repeats) for prompt in speed_prompts()],
        guardrail_verdicts=[guardrail_verdict(case, model_client) for case in guardrail_cases],
    )


def verdict_label(verdict: GuardrailVerdict) -> str:
    if verdict.model_failed:
        return "failed: model unavailable"
    if not verdict.kept_every_fact:
        return "rejected: dropped or changed a fact"
    if not verdict.added_no_number:
        return "rejected: added a number"
    if not verdict.added_no_name:
        return "rejected: added a name"
    return "kept"


def table_cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def rate_cell(rate: float) -> str:
    return str(int(rate)) if float(rate).is_integer() else str(rate)


def percent(part: int, whole: int) -> str:
    return f"{round(100 * part / whole)}%" if whole else "n/a"


def judged_verdicts(verdicts: list[GuardrailVerdict]) -> list[GuardrailVerdict]:
    return [verdict for verdict in verdicts if not verdict.model_failed]


def rejection_rate_line(all_verdicts: list[GuardrailVerdict]) -> str:
    verdicts = judged_verdicts(all_verdicts)
    rejected_count = sum(not verdict.kept for verdict in verdicts)
    return f"Guardrail rejection rate: {rejected_count} of {len(verdicts)} replies ({percent(rejected_count, len(verdicts))})"


def median_of(values: list[float]) -> float:
    return statistics.median(values)


def speed_rows(speed_results: list[SpeedResult]) -> list[str]:
    rows = []
    for speed_result in speed_results:
        prompt_tokens = estimated_prompt_tokens(speed_result.prompt.messages)
        failed_cell = str(speed_result.failed_stream_count)
        if not speed_result.timings:
            rows.append(f"| {speed_result.prompt.name} | {prompt_tokens} | {NO_REPLY_CELL} | {NO_REPLY_CELL} | 0 | {failed_cell} |")
            continue
        first_token_seconds = [timing.seconds_to_first_token for timing in speed_result.timings]
        tokens_per_second = [timing.tokens_per_second for timing in speed_result.timings]
        token_counts = [timing.streamed_token_count for timing in speed_result.timings]
        rows.append(
            f"| {speed_result.prompt.name} | {prompt_tokens} "
            f"| {median_of(first_token_seconds):.3f} ({min(first_token_seconds):.3f}–{max(first_token_seconds):.3f}) "
            f"| {median_of(tokens_per_second):.1f} ({min(tokens_per_second):.1f}–{max(tokens_per_second):.1f}) "
            f"| {median_of(token_counts):.0f} | {failed_cell} |"
        )
    return rows


def rejection_reason_rows(verdicts: list[GuardrailVerdict]) -> list[str]:
    labels = [verdict_label(verdict) for verdict in verdicts]
    return [f"| {label} | {labels.count(label)} |" for label in sorted(set(labels))]


def rejection_rate_by_rate_rows(verdicts: list[GuardrailVerdict]) -> list[str]:
    rows = []
    for rate in sorted({verdict.case.rate for verdict in verdicts}, reverse=True):
        verdicts_at_rate = [verdict for verdict in judged_verdicts(verdicts) if verdict.case.rate == rate]
        rejected_count = sum(not verdict.kept for verdict in verdicts_at_rate)
        rows.append(
            f"| {rate_cell(rate)} | {rejected_count} of {len(verdicts_at_rate)} "
            f"({percent(rejected_count, len(verdicts_at_rate))}) |"
        )
    return rows


def verdict_rows(verdicts: list[GuardrailVerdict]) -> list[str]:
    return [
        f"| {rate_cell(verdict.case.rate)} | {table_cell(verdict.case.question)} "
        f"| {table_cell(verdict.reply)} | {verdict_label(verdict)} |"
        for verdict in verdicts
    ]


def guardrail_run_description(verdicts: list[GuardrailVerdict]) -> str:
    distinct_cases = {verdict.case for verdict in verdicts}
    question_count = len({case.question for case in distinct_cases})
    rate_count = len({case.rate for case in distinct_cases})
    times_each = len(verdicts) // len(distinct_cases) if distinct_cases else 0
    return (
        f"{len(verdicts)} replies: {question_count} fixed Rate questions at {rate_count} Rates, "
        f"each asked {'once' if times_each == 1 else f'{times_each} times'}"
    )


def memory_lines(memory: MemoryReading) -> list[str]:
    footprint_text = "not measured" if memory.footprint_megabytes is None else f"{memory.footprint_megabytes:.1f} MB"
    return [
        f"- Peak resident memory of llama-server: {memory.peak_resident_megabytes:.1f} MB",
        f"- macOS memory footprint of llama-server at the end of the run: {footprint_text}",
    ]


def results_markdown(
    result: BenchmarkResult,
    machine: MachineDescription,
    memory: MemoryReading,
    model_load_seconds: float,
    benchmark_date: date,
) -> str:
    first_speed_result = result.speed_results[0] if result.speed_results else None
    speed_repeats = len(first_speed_result.timings) + first_speed_result.failed_stream_count if first_speed_result else 0
    lines = [
        "# T5: Mac model benchmark",
        "",
        f"Run on {benchmark_date.isoformat()} with `.venv/bin/python -m travel_companion.model_benchmark`.",
        "",
        "## Machine",
        "",
        f"- Chip: {machine.chip}",
        f"- Memory: {machine.memory_gigabytes} GB",
        f"- OS: {machine.os_version}",
        f"- llama-server: {machine.llama_server_version}",
        f"- Model: `{machine.model_file}`, 2,048-token context, all layers on the GPU (`scripts/start_model_server.sh`)",
        "",
        "## Summary",
        "",
        f"- Model load time: {model_load_seconds:.1f} s (from starting llama-server until `/health` answers)",
        *memory_lines(memory),
        f"- {rejection_rate_line(result.guardrail_verdicts)}",
        "",
        "Resident memory is sampled from `ps` every 0.1 s for the whole run and includes the memory-mapped model "
        "weights. The footprint (from `footprint`) counts only memory macOS cannot reclaim by dropping clean "
        "file-backed pages, so it leaves the weights out.",
        "",
        "## Speed",
        "",
        f"Each prompt was streamed {speed_repeats} times with the prompt cache off, after one warm-up request. "
        "Values are the median, with the range in brackets. Time to first token is measured by the client from "
        "sending the request to the first streamed content chunk. Tokens per second counts streamed chunks after "
        "the first, divided by the time between the first and last chunk. Prompt tokens are the app's own estimate "
        "(`prompt_budget.py`).",
        "",
        "| Prompt | Prompt tokens (estimate) | Time to first token, s | Tokens per second | Reply tokens | Failed streams |",
        "| --- | --- | --- | --- | --- | --- |",
        *speed_rows(result.speed_results),
        "",
        "## Guardrail on real-model output",
        "",
        f"{guardrail_run_description(result.guardrail_verdicts)}, through the same prompt and checks as "
        "`POST /api/ask/rate`, with llama-server's default sampling. A rejected reply is replaced by the template "
        "answer on the card, so the user still sees the correct Rate.",
        "",
        "| Verdict | Replies |",
        "| --- | --- |",
        *rejection_reason_rows(result.guardrail_verdicts),
        "",
        "| Rate | Rejected |",
        "| --- | --- |",
        *rejection_rate_by_rate_rows(result.guardrail_verdicts),
        "",
        "### Every reply",
        "",
        "| Rate | Question | Model reply | Verdict |",
        "| --- | --- | --- | --- |",
        *verdict_rows(result.guardrail_verdicts),
        "",
    ]
    return "\n".join(lines)


class ResidentMemorySampler:
    def __init__(self, process_id: int) -> None:
        self.process_id = process_id
        self.peak_resident_kilobytes = 0
        self.stopping = threading.Event()
        self.thread = threading.Thread(target=self.sample_until_stopped, daemon=True)

    def resident_kilobytes(self) -> int:
        ps_output = subprocess.run(
            ["ps", "-o", "rss=", "-p", str(self.process_id)], capture_output=True, text=True
        ).stdout.strip()
        return int(ps_output) if ps_output.isdigit() else 0

    def sample_until_stopped(self) -> None:
        while not self.stopping.is_set():
            self.peak_resident_kilobytes = max(self.peak_resident_kilobytes, self.resident_kilobytes())
            self.stopping.wait(MEMORY_SAMPLE_INTERVAL_SECONDS)

    def start(self) -> "ResidentMemorySampler":
        self.thread.start()
        return self

    def stop(self) -> float:
        self.stopping.set()
        self.thread.join()
        return self.peak_resident_kilobytes / KILOBYTES_PER_MEGABYTE


def footprint_megabytes(process_id: int) -> float | None:
    footprint_output = subprocess.run(["footprint", "-p", str(process_id)], capture_output=True, text=True).stdout
    match = FOOTPRINT_PATTERN.search(footprint_output)
    if match is None:
        return None
    return float(match.group(1)) * FOOTPRINT_UNIT_MEGABYTES[match.group(2)]


def command_output(command: list[str]) -> str:
    return subprocess.run(command, capture_output=True, text=True).stdout.strip()


def llama_server_version() -> str:
    version_output = subprocess.run(["llama-server", "--version"], capture_output=True, text=True)
    version_lines = (version_output.stdout + version_output.stderr).splitlines()
    return next((line.removeprefix("version: ") for line in version_lines if line.startswith("version:")), "unknown")


def this_machine(model_path: Path) -> MachineDescription:
    return MachineDescription(
        chip=command_output(["sysctl", "-n", "machdep.cpu.brand_string"]),
        memory_gigabytes=int(command_output(["sysctl", "-n", "hw.memsize"])) // 1024**3,
        os_version=f"macOS {platform.mac_ver()[0]}",
        llama_server_version=llama_server_version(),
        model_file=model_path.name,
    )


def benchmark_model_path() -> Path:
    models_dir = Path(os.environ.get("MODELS_DIR", REPO_ROOT / "models"))
    return Path(os.environ.get("MODEL_PATH", models_dir / "qwen2.5-1.5b-instruct-q4_k_m.gguf"))


def server_is_healthy(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1.0) as health_response:
            return health_response.status == 200
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        return False


def port_is_free(port: int) -> bool:
    return not server_is_healthy(port) and subprocess.run(
        ["lsof", "-iTCP:" + str(port), "-sTCP:LISTEN"], capture_output=True
    ).returncode != 0


def wait_until_healthy(server: subprocess.Popen, port: int) -> None:
    deadline = time.monotonic() + SERVER_START_TIMEOUT_SECONDS
    while not server_is_healthy(port):
        if server.poll() is not None:
            raise RuntimeError(f"llama-server exited with code {server.returncode} before it was ready")
        if time.monotonic() > deadline:
            raise RuntimeError(f"llama-server was not ready after {SERVER_START_TIMEOUT_SECONDS:.0f} s")
        time.sleep(0.05)


def stop_server(server: subprocess.Popen) -> None:
    server.terminate()
    try:
        server.wait(timeout=SERVER_STOP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()


def benchmark_against_llama_server(port: int, speed_repeats: int, guardrail_repeats: int, results_path: Path) -> None:
    if not port_is_free(port):
        raise SystemExit(f"Port {port} is already in use. Pass --port to pick another.")
    model_path = benchmark_model_path()
    endpoint_url = f"http://127.0.0.1:{port}/v1/chat/completions"
    server_environment = {**os.environ, "MODEL_PORT": str(port), "MODEL_PATH": str(model_path)}
    with tempfile.TemporaryFile() as server_log:
        started_at = time.perf_counter()
        server = subprocess.Popen(
            [str(START_MODEL_SERVER_SCRIPT)], env=server_environment, stdout=server_log, stderr=server_log
        )
        try:
            memory_sampler = ResidentMemorySampler(server.pid).start()
            wait_until_healthy(server, port)
            model_load_seconds = time.perf_counter() - started_at
            for prompt in speed_prompts():
                timed_stream_or_none(endpoint_url, prompt.messages)
            result = run_benchmark(endpoint_url, fixed_guardrail_cases(guardrail_repeats), speed_repeats)
            memory = MemoryReading(
                peak_resident_megabytes=memory_sampler.stop(), footprint_megabytes=footprint_megabytes(server.pid)
            )
        finally:
            stop_server(server)
    markdown = results_markdown(result, this_machine(model_path), memory, model_load_seconds, date.today())
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(markdown)
    print(f"{rejection_rate_line(result.guardrail_verdicts)}. Results written to {results_path}")


def parsed_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark the real model on the Mac and write docs/results.")
    parser.add_argument("--port", type=int, default=DEFAULT_BENCHMARK_PORT)
    parser.add_argument("--speed-repeats", type=int, default=DEFAULT_SPEED_REPEATS)
    parser.add_argument("--guardrail-repeats", type=int, default=DEFAULT_GUARDRAIL_REPEATS)
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULTS_PATH)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parsed_arguments()
    benchmark_against_llama_server(
        arguments.port, arguments.speed_repeats, arguments.guardrail_repeats, arguments.output
    )
