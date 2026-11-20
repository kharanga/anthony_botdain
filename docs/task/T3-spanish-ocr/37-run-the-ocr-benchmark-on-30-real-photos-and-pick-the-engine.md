# #37: Run the OCR benchmark on 30+ real photos and pick the engine

**Parent:** #4  
**Status:** open  
**Labels:** human  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/37

## Parent

#4

## What to build

The user takes 30+ real menu and receipt photos and types their transcriptions into the data folder. An agent then runs the benchmark, records the engine choice in `docs/results/`, and switches engines if PaddleOCR wins.

## Acceptance criteria

- [ ] 30+ real photos with transcriptions are in the data folder (not committed)
- [ ] Benchmark results for the real set are in `docs/results/`
- [ ] The chosen engine is recorded and wired in

## Blocked by

- #36

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
