# #26: Add and unlock a document

**Parent:** #10  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/26

## Parent

#10

## What to build

The user sets a 6-digit PIN on first use and adds a specimen document photo, which is encrypted at rest. A locked vault returns nothing; the PIN unlocks it and shows the document in a card.

## Acceptance criteria

- [ ] First use asks for a 6-digit PIN
- [ ] A specimen document can be added and is encrypted at rest
- [ ] A locked vault returns no documents through the API
- [ ] The right PIN unlocks the vault and shows the document; a wrong PIN does not
- [ ] A test checks that no plaintext document is on disk

## Blocked by

- #21
