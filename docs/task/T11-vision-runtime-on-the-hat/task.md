# #11: T11: Vision runtime on the HAT

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/11

Part of #1.

## What to build

Qwen2-VL-2B on the AI HAT+ 2 through `hailo-ollama` (install `hailo-h10-all`, not `hailo-all`; pre-compiled Model Zoo models only), with a matching vision model on the Mac behind the same endpoint.

## Blocked by

#5 (T5)

## Done when

- HAT vs. CPU latency, watts and quality measured
- Spanish OCR quality of the vision model compared with T3

## User stories

10, 11 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
