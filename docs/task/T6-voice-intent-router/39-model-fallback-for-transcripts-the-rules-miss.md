# #39: Model fallback for transcripts the rules miss

**Parent:** #7  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/39

## Parent

#7

## What to build

When no rule matches, the router asks the model endpoint to pick exactly one of the six intent labels or none. An invalid or invented label, or the model being down, gives "I can't do that yet" plus the list.

## Acceptance criteria

- [ ] A paraphrase the rules miss is routed by the model, tested with the fake server
- [ ] An invalid or invented label gives "I can't do that yet"
- [ ] Model unavailable gives "I can't do that yet", not an error
- [ ] The prompt fits the 2,048-token budget

## Blocked by

- #38

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
