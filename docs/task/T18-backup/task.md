# #14: T18: Backup

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/14

Part of #1.

## What to build

A Back up tile writes an encrypted copy of the data folder (expenses, captured photos, router labels, vault) to a USB stick. The vault stays encrypted under the PIN inside the backup. Includes restore.

## Blocked by

#10 (T8), #9 (T9)

## Done when

- A backup and restore round-trip test passes
- A restore has been done once on the real device

## User stories

75–77 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
