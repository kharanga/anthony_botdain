# #40: "Show my allergy card" opens the staff phrase card

**Parent:** #7  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/40

## Parent

#7

## What to build

Saying (or sending the transcript) "show my allergy card" returns the staff phrase card, and the UI shows it.

## Acceptance criteria

- [ ] The transcript "show my allergy card" and its sample variants return the staff phrase card through the HTTP API
- [ ] The UI opens the card in large text

## Blocked by

- #31
- #38

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
