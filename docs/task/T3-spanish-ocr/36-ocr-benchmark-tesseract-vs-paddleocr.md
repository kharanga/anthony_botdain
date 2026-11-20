# #36: OCR benchmark: Tesseract vs PaddleOCR

**Parent:** #4  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/36

## Parent

#4

## What to build

A benchmark tool runs Tesseract `spa` and PaddleOCR over a folder of photos, each with a hand-typed transcription, and reports character error rate, Allergen Term recall and false positives, comparing accent-aware with accent-insensitive matching. It runs on the specimen set in the repo, or on real photos in the gitignored data folder, and writes results to `docs/results/`.

## Acceptance criteria

- [ ] The benchmark runs on the specimen set and writes a results file to `docs/results/`
- [ ] It reports character error rate, Allergen Term recall and false positives per engine
- [ ] Accent-aware and accent-insensitive matching are compared
- [ ] It reads real photos and transcriptions from the data folder without committing them
- [ ] The transcription format for real photos is documented

## Blocked by

- #30
- #35

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
