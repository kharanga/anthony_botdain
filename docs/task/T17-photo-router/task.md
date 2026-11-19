# #12: T17: Photo router

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/12

Part of #1.

## What to build

Every photo gets a Suggested Kind: OCR first, then keyword rules (receipt clues: total, subtotal, IVA, factura, cédula jurídica, ₡/$ amounts; menu clues: several lines each with a price and a food word), then the vision model only when the rules are unsure. The vision model must answer with exactly one of: menu, receipt, ticket, sign, document, other.

The user confirms the Suggested Kind, cycles through menu ↔ receipt ↔ ticket ↔ sign ↔ document ↔ other and confirms one, or retakes. Nothing runs until a kind is confirmed. The cycle starts on menu when the router is unsure. A spoken question that names the kind skips the router.

Routing: menu → scanner, receipt → expenses, ticket/document → vault, sign/other → Capture Mode. Every photo is saved with GPS position, time, Suggested Kind and Photo Kind in the gitignored data folder.

## Blocked by

#4 (T3), #5 (T5), #11 (T11)

## Done when

- ≥95% of suggestions match the confirmed kind on the labelled set
- Menus suggested as something else counted separately

## User stories

1–11, 72–74 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
