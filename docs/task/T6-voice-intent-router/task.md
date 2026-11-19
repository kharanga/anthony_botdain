# #7: T6: Voice + intent router

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/7

Part of #1.

## What to build

whisper.cpp on the CPU (English only) plus a rules-first intent router with LLM fallback. Exactly six intents: show the staff phrase, allergen question about the last menu, guide question, add an expense, spending question, open the vault (PIN still required). Anything else gets "I can't do that yet" plus the list. The arcade button over GPIO is push-to-talk only.

## Blocked by

#2 (T1), #5 (T5)

## Done when

- 50 sample questions routed correctly, with latency measured
- Tests send text transcripts; speech-to-text accuracy is a separate benchmark

## User stories

8, 31, 42, 44–49, 63, 64, 70 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
