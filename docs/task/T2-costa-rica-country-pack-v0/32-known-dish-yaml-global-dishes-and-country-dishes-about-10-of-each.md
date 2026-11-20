# #32: Known Dish YAML: Global Dishes and country dishes, about 10 of each

**Parent:** #3  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/32

## Parent

#3

## What to build

Known Dishes live in YAML in two groups: Global Dishes shared by every Country Pack, and country dishes in the `cr` pack. They merge at load, and a country dish with the same name replaces the Global Dish. Each dish has aliases, Ingredients marked usual or sometimes, a recorded source and a reviewed flag. Seed about 10 of each group. A dish lookup by name (via aliases, ignoring accents and case) returns a card with its Ingredients and source as evidence, and says "unreviewed" when the dish is not reviewed. A results file lists the dishes still to review.

## Acceptance criteria

- [ ] Global and country dishes load from YAML and merge, with country dishes replacing same-name Global Dishes
- [ ] Schema tests fail when a dish has no source or an Ingredient isn't marked usual or sometimes
- [ ] Lookup through an alias, ignoring accents and case, returns the dish card with its source
- [ ] An unreviewed dish's card says "unreviewed"; setting `reviewed: true` in the YAML removes it
- [ ] A results file in `docs/results/` lists every unreviewed dish
- [ ] About 10 Global Dishes and about 10 Costa Rica dishes are seeded

## Blocked by

- #30

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
