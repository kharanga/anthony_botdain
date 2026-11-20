# #10: T8: Encrypted document vault

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/10

## Tickets

- #26 Add and unlock a document (closed)
- #27 Vault auto-lock (closed)
- #28 Full-brightness ticket view (closed)

Part of #1.

## What to build

Encrypted storage for ticket and document photos. 6-digit PIN. Auto-lock after 2 minutes of no use. A full-brightness view for QR codes and barcodes. Specimen documents only in the repo; real ones only in the gitignored data folder.

## Blocked by

#2 (T1)

## Done when

- Locked vault returns nothing without the PIN
- Auto-lock tested with injected time
- Nothing outside the vault is stored unencrypted

## User stories

66–71 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
