# #38: Rules-first intent router over text transcripts

**Parent:** #7  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/38

## Parent

#7

## What to build

Sending a text transcript returns an answer card naming one of exactly six intents (show the staff phrase, allergen question about the last menu, guide question, add an expense, spending question, open the vault) with the details pulled out (dish number, amount, category…). Anything else returns "I can't do that yet" plus the list of six. The intent handlers come in later tasks. 50 sample questions are written down, tested, and their routing latency is written to `docs/results/`.

## Acceptance criteria

- [ ] A transcript through the HTTP API returns a card naming the intent and its details
- [ ] Unmatched transcripts return "I can't do that yet" plus the six intents
- [ ] 50 sample questions are committed and all route correctly in tests
- [ ] Routing latency for the samples is written to `docs/results/`
- [ ] No model call is made when a rule matches

## Blocked by

- None (can start immediately)

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
