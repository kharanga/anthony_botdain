# T6: Speech-to-text accuracy and latency

Run on 2026-11-19 with `.venv/bin/python -m travel_companion.speech_benchmark`.

## Machine

- arm64, Darwin 27.2.0
- Python 3.13.2
- whisper.cpp `whisper-cli` from Homebrew, model `ggml-base.en.bin`, English only, CPU only (`-ng`)

## Method

12 sample questions from `specimens/intent_samples.toml` are spoken by macOS `say` (voice Samantha) into 16 kHz mono WAV files at benchmark time; they are synthetic, so no real voice is recorded or committed. Each file goes through the same `whisper-cli` call that `POST /api/speech` makes, after one warm-up call. Latency is wall time for that call, including loading the model, because the app starts `whisper-cli` once per question. Word error rate compares lowercase words with punctuation removed, so "five" against "5" counts as an error. "Routes the same" checks that the cleaned transcript reaches the same intent with the same details (compared as lowercase words) as the typed sample, which is what the user sees; it uses the rules only, with no model fallback, so a misheard word is not rescued by the model.

Synthetic speech is cleaner than a real voice in a restaurant, so these numbers are a best case. Measure again with real recordings and the USB mic in T15.

## Summary

- Word error rate: 6 errors in 72 words (8.3%)
- Routes the same as the typed question: 9 of 12
- Median latency: 1.37 s; slowest 1.66 s
- Median real-time factor (latency / audio length): 0.67

## Per sample

| Spoken | whisper.cpp heard | Word errors | Routes the same | Audio, s | Latency, s |
| --- | --- | --- | --- | --- | --- |
| show my allergy card | Show my allergy card. | 0 | yes | 1.6 | 1.06 |
| I need to tell the waiter about my allergy | I need to tell the waiter about my allergy. | 0 | yes | 2.5 | 1.29 |
| Does number 4 have lobster | Does number 4 have Lobster? | 0 | yes | 1.7 | 1.14 |
| does the ceviche have shrimp | Does the Saviche have shrimp? | 1 | NO | 1.7 | 1.32 |
| Where can I see sloths near La Fortuna? | Where can I see sloughs near law for tuna? | 4 | NO | 2.6 | 1.49 |
| is the tap water drinkable in Tamarindo | is the tap water drinkable in Tamarindo. | 0 | yes | 2.5 | 1.42 |
| how much does a taxi from the airport cost? | How much does a taxi from the airport cost? | 0 | yes | 2.7 | 1.38 |
| spent 5 rojos at the soda | Spent 5 rojos at the soda. | 0 | yes | 1.9 | 1.36 |
| I just spent 15,000 colones on souvenirs | I just spent 15,000 colonas on souvenirs. | 1 | NO | 3.2 | 1.66 |
| what's my total spending | What's my total spending? | 0 | yes | 1.6 | 1.42 |
| open my passport | Open my passport. | 0 | yes | 1.4 | 1.31 |
| where's my driver's license | Where's my driver's license? | 0 | yes | 1.8 | 1.39 |
