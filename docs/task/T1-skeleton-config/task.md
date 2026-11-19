# #2: T1: Skeleton + config

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/2

Part of #1.

## What to build

Project skeleton on the Mac: a FastAPI backend, a local web UI shell, DuckDB setup, and the answer card shape every feature returns (each card carries its evidence).

Config: country=cr, active Allergens=[shellfish], home currency=USD, Rate (colones per dollar, editable), PIN settings, model endpoint URL.

## Blocked by

None

## Done when

- The app starts on the Mac and serves the UI shell in a browser tab
- Config loads with the values above
- An answer card round-trips through the HTTP API with an evidence field
- A fresh clone runs with fake data alone

## User stories

83, 84 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
