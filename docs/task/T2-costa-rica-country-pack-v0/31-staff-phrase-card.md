# #31: Staff phrase card

**Parent:** #3  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/31

## Parent

#3

## What to build

The three Trip Build Phrases live in the pack YAML with their Spanish text and their Machine-checked status. A request returns the staff phrase card, and the UI shows it in large text that staff can read at arm's length, with the Machine-checked status visible.

## Acceptance criteria

- [ ] The three Phrases from SPEC.md load from the pack YAML
- [ ] The phrase card comes back through the HTTP API with each Phrase and its Machine-checked status as evidence
- [ ] The UI shows the card in large text, reachable in one tap from the shell
- [ ] Editing a Phrase in the YAML changes the card

## Blocked by

- #30

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
