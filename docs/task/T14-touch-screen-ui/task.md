# #13: T14: Touch-screen UI

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/13

Part of #1.

## What to build

Home screen with six large tiles: Scan, Allergy card, Guide, Expenses, Vault, Back up. Answer cards, large touch targets, a dark theme and idle dimming. The allergy card text is readable at arm's length.

## Blocked by

#6 (T4), #7 (T6), #10 (T8), #9 (T9), #8 (T10), #12 (T17)

## Done when

- Every Trip Build feature is reachable in one tap from home

## User stories

39–43, 78, 79 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
