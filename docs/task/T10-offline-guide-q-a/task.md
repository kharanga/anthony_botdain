# #8: T10: Offline guide Q&A

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/8

Part of #1.

## What to build

Keyword search over the Wikivoyage Costa Rica ZIM (via Kiwix) returns the top 2–3 passages. The LLM writes a 1–2 sentence summary drawn only from those passages. The card shows the passages and article names as evidence. No match gives "not in my guide". CC BY-SA attribution is shown in the app.

## Blocked by

#3 (T2), #5 (T5)

## Done when

- A zero-match question returns "not in my guide"
- The summary is grounded in the returned passages
- Prompt plus passages fit 2,048 tokens

## User stories

50–54 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
