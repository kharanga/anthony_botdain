# #16: T16: Ship

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/16

Part of #1.

## What to build

README, demo video, results, attributions. A fresh clone runs on the Mac with fake data. After the trip, write the post-trip spec from the Backlog and the captured data.

## Blocked by

#15 (T15)

## Done when

- A fresh clone passes all tests on the Mac
- Attributions cover Wikivoyage and dish sources

## User stories

83, 84 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
