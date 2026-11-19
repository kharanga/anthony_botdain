from datetime import date

from travel_companion.model_benchmark import (
    GuardrailCase,
    MachineDescription,
    MemoryReading,
    results_markdown,
    run_benchmark,
)

MACHINE = MachineDescription(
    chip="Apple M2",
    memory_gigabytes=8,
    os_version="macOS 27.2",
    llama_server_version="1.0.0 (build 12359)",
    model_file="qwen2.5-1.5b-instruct-q4_k_m.gguf",
)
MEMORY = MemoryReading(peak_resident_megabytes=1234.5, footprint_megabytes=133.0)
BENCHMARK_DATE = date(2026, 11, 18)


def benchmark_markdown(fake_model, guardrail_cases, speed_repeats=1):
    result = run_benchmark(
        fake_model.endpoint_url,
        guardrail_cases=guardrail_cases,
        speed_repeats=speed_repeats,
    )
    return results_markdown(result, MACHINE, MEMORY, model_load_seconds=2.5, benchmark_date=BENCHMARK_DATE)


def script_speed_replies(fake_model, speed_repeats=1):
    fake_model.reply_with(*["Hola, pura vida."] * (3 * speed_repeats))


def test_the_guardrail_rejection_rate_counts_replies_that_drop_or_change_a_fact(fake_model):
    script_speed_replies(fake_model)
    fake_model.reply_with(
        "One US dollar buys ₡510.",
        "One US dollar buys ₡520.",
        "At Banco Nacional one US dollar buys ₡498.",
        "Each US dollar is worth 498 colones.",
    )
    cases = [
        GuardrailCase(rate=510, question="What is the rate?"),
        GuardrailCase(rate=510, question="How many colones for a dollar?"),
        GuardrailCase(rate=498, question="What is the rate?"),
        GuardrailCase(rate=498, question="How many colones for a dollar?"),
    ]

    markdown = benchmark_markdown(fake_model, cases)

    assert "Guardrail rejection rate: 2 of 4 replies (50%)" in markdown
    assert "4 replies: 2 fixed Rate questions at 2 Rates, each asked once" in markdown
    assert "| 510 | How many colones for a dollar? | One US dollar buys ₡520. | rejected: dropped or changed a fact |" in markdown
    assert "| 498 | What is the rate? | At Banco Nacional one US dollar buys ₡498. | rejected: added a name |" in markdown
    assert "| 510 | What is the rate? | One US dollar buys ₡510. | kept |" in markdown


def test_speed_and_memory_are_recorded(fake_model):
    script_speed_replies(fake_model, speed_repeats=2)
    fake_model.reply_with("One US dollar buys ₡510.")

    markdown = benchmark_markdown(fake_model, [GuardrailCase(rate=510, question="What is the rate?")], speed_repeats=2)

    assert "Time to first token" in markdown
    assert "Tokens per second" in markdown
    assert "Peak resident memory of llama-server: 1234.5 MB" in markdown
    assert "Model load time: 2.5 s" in markdown
    assert "Apple M2" in markdown
    assert "2026-11-18" in markdown
    speed_requests = [request for request in fake_model.received_requests if request.get("stream")]
    assert len(speed_requests) == 6


def test_reply_text_cannot_break_the_results_table(fake_model):
    script_speed_replies(fake_model)
    fake_model.reply_with("One US dollar | buys ₡510.\nPura vida!")

    markdown = benchmark_markdown(fake_model, [GuardrailCase(rate=510, question="What is the rate?")])

    assert "| 510 | What is the rate? | One US dollar \\| buys ₡510. Pura vida! | kept |" in markdown
