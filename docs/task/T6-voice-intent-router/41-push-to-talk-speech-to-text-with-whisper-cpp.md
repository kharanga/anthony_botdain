# #41: Push-to-talk speech-to-text with whisper.cpp

**Parent:** #7  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/41

## Parent

#7

## What to build

Holding a push-to-talk control in the UI records from the Mac mic; releasing it sends the audio to whisper.cpp on the CPU (English only), and the transcript goes through the intent router. Includes a script to fetch the whisper model and a speech-to-text benchmark on recorded samples. Tests still send text transcripts; a real-whisper test runs only when opted in. The GPIO arcade button is out of scope until the Pi is in use.

## Acceptance criteria

- [ ] Holding and releasing the UI push-to-talk control returns the routed answer card
- [ ] whisper.cpp runs locally with no network call
- [ ] A model fetch script and start instructions are in the README
- [ ] Speech-to-text accuracy and latency on recorded samples are written to `docs/results/`
- [ ] The real-whisper test is skipped unless opted in

## Blocked by

- #38

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
