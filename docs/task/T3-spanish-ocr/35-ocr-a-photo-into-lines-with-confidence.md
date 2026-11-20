# #35: OCR a photo into lines with confidence

**Parent:** #4  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/35

## Parent

#4

## What to build

Uploading a photo returns an answer card with its OCR lines, each with a confidence score, using Tesseract `spa` (install with `brew install tesseract-lang`). The OCR engine sits behind a small interface so another engine can replace it. Lines below a confidence threshold are flagged so the scanner can give them Ask staff. Test images committed to the repo are generated fake menus and receipts only.

## Acceptance criteria

- [ ] A photo uploaded through the HTTP API returns a card of OCR lines with per-line confidence
- [ ] Low-confidence lines are flagged, with the threshold set in config
- [ ] Accented Spanish text on a specimen menu comes back correctly
- [ ] Only generated or specimen images are committed

## Blocked by

- #30

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
