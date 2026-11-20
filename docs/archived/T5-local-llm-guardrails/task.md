# #5: T5: Local LLM + guardrails

**Parent:** #1  
**Status:** closed  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/5

## Tickets

- #22 Model endpoint with a fake server (closed)
- #23 Fact guardrail (closed)
- #24 Real llama.cpp on the Mac (closed)
- #25 Mac model benchmark (closed)

Part of #1.

## What to build

One OpenAI-compatible model endpoint set in config (ADR 0001). On the Mac: llama.cpp server with Qwen2.5-1.5B (GGUF, Q4_K_M). On the Pi: `hailo-ollama` with Qwen2.5-1.5B. Prompts fit the 2,048-token context.

## Blocked by

#2 (T1)

## Done when

- Speed, memory and quality benchmarked on both machines
- Tests check that facts in answers come from data and are not altered by the LLM
- A fake endpoint server is available for tests

## User stories

36, 48 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
