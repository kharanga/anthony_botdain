# #34: Costa Rica dishes, about 100

**Parent:** #3  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/34

## Parent

#3

## What to build

An agent picks and writes about 100 Costa Rica dishes, weighted toward sodas (casado, gallo pinto, olla de carne, chifrijo) and coastal and Caribbean food (rice and beans, rondón, ceviche, arroz con mariscos), from Wikipedia's Costa Rican cuisine articles, Wikibooks Cookbook and the Wikivoyage "Eat" sections. Every dish records its source and starts unreviewed. Ceviche de pescado is marked Often contains for shellfish.

## Acceptance criteria

- [ ] About 100 Costa Rica dishes are in the `cr` pack YAML and pass the schema tests
- [ ] Every dish has a recorded source and starts unreviewed
- [ ] Common menu spellings and abbreviations are aliases (e.g. "arroz c/ camarones")
- [ ] Ceviche de pescado has shellfish as a sometimes Ingredient
- [ ] The unreviewed list in `docs/results/` is updated

## Blocked by

- #32

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
