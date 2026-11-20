# #33: Global Dishes, about 50

**Parent:** #3  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/33

## Parent

#3

## What to build

An agent picks and writes about 50 Global Dishes: generic restaurant dishes where shrimp hides without being named (pasta, pizza, burgers, sushi, fajitas, fried rice, pad thai, paella, soups and sauces…). Every dish records a source for its Ingredients and starts unreviewed.

## Acceptance criteria

- [ ] About 50 Global Dishes are in the YAML and pass the schema tests
- [ ] Every dish has a recorded source and starts unreviewed
- [ ] Dishes where shrimp or seafood broth is common but not named are marked with the right usual or sometimes Ingredients
- [ ] The unreviewed list in `docs/results/` is updated

## Blocked by

- #32

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
