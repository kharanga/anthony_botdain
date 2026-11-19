# #4: T3: Spanish OCR

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/4

Part of #1.

## What to build

Benchmark Tesseract `spa` against PaddleOCR (and the HAT vision model on the Pi, once T11 exists) on 30+ real menu and receipt photos. Pick one and wire it in, with per-line confidence.

## Blocked by

#2 (T1)

## Done when

- Results written to the results folder
- Accent-aware and accent-insensitive matching compared
- Low-confidence lines are flagged so the scanner can give them Ask staff

## User stories

20, 22 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
