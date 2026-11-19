# #15: T15: Pi port + measurements

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/15

Part of #1.

## What to build

Port to the Pi 5 with the AI HAT+ 2, Camera Module 3, USB GPS and USB mic. Chromium kiosk mode. Start by about day 9.

## Blocked by

#13 (T14), #14 (T18)

## Done when

- Every Trip Build feature passes with airplane mode on
- Latency and power measured per feature
- ≥4 hours of mixed use on the power bank with `vcgencmd get_throttled` = 0

## User stories

80–82 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
