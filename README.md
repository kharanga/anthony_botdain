# travel-companion

An offline travel companion. The plan is in `SPEC.md`; project terms are in `GLOSSARY.md`.

## Run on the Mac with fake data

Photo OCR needs Tesseract with Spanish data, and the tests run it for real:

```sh
brew install tesseract tesseract-lang
```

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest -q
.venv/bin/travel-companion
```

The app serves on http://127.0.0.1:8765. Set `TRAVEL_COMPANION_CONFIG` to use a config other than `config/default.toml`.

## Real model on the Mac (llama.cpp)

The app talks to one OpenAI-compatible model endpoint set in config (`[model] endpoint_url`, see `docs/adr/0001-one-model-endpoint.md`). On the Mac that is llama.cpp's `llama-server` running Qwen2.5-1.5B-Instruct (GGUF, Q4_K_M).

1. Install llama.cpp:

   ```sh
   brew install llama.cpp
   ```

2. Download the model (about 1.1 GB) into the gitignored `models/` folder. The script checks its SHA-256 and does nothing if the file is already there:

   ```sh
   scripts/fetch_model.sh
   ```

   It comes from the official `Qwen/Qwen2.5-1.5B-Instruct-GGUF` repo on Hugging Face. Set `MODELS_DIR` to keep models somewhere else, for example one shared folder for several checkouts.

3. Start the server:

   ```sh
   scripts/start_model_server.sh
   ```

   It runs with `--offline`, so it makes no network calls, listens on 127.0.0.1:8080 and uses a 2,048-token context to match the AI HAT+ 2. `MODEL_PORT`, `MODELS_DIR` and `MODEL_PATH` override the defaults. It uses about 1 GB of RAM. Stop it with Ctrl-C.

4. Start the app. `config/default.toml` already points at `http://127.0.0.1:8080/v1/chat/completions`; if the server runs elsewhere, change only `endpoint_url`.

   ```sh
   .venv/bin/travel-companion
   curl -s http://127.0.0.1:8765/api/ask -H 'Content-Type: application/json' -d '{"question": "What does pura vida mean?"}'
   ```

### Test against the real model

The normal test run uses a scripted fake endpoint. The tests in `tests/test_real_model.py` are skipped unless you point them at a running server:

```sh
TRAVEL_COMPANION_REAL_MODEL_URL=http://127.0.0.1:8080/v1/chat/completions .venv/bin/pytest -q tests/test_real_model.py
```

### Benchmark the real model

```sh
MODELS_DIR=/path/to/models .venv/bin/python -m travel_companion.model_benchmark
```

It starts its own llama-server on port 8091 (`--port` to change it), measures time to first token, tokens per second, load time and peak memory, then asks a fixed set of Rate questions through the fact guardrail and records how often it rejects the model's reply. It stops the server when it finishes and rewrites `docs/results/T5-mac-model-benchmark.md`. `--speed-repeats` and `--guardrail-repeats` set how many times each prompt runs.

## Known Dishes YAML

Global Dishes, shared by every Country Pack, live in `packs/global/dishes.yaml`. Country dishes live in `packs/<country>/dishes.yaml`. Both files are a YAML list of dishes in this shape:

```yaml
- name: Gallo pinto
  aliases: [pinto]
  ingredients:
    rice: usual
    black beans: usual
    egg: sometimes
  source: https://en.wikipedia.org/wiki/Gallo_pinto
  reviewed: false
```

- `name` and `source` are required. `source` is where the entry came from (a Wikipedia, Wikibooks or Wikivoyage URL).
- `aliases` is optional: other names a menu might use. Lookup ignores accents and case, so don't list accent or case variants.
- `ingredients` maps each Ingredient (lowercase English) to `usual` (almost always in the dish) or `sometimes` (depends on the kitchen). Name crustaceans plainly: shrimp, lobster, crab, langoustine.
- `reviewed` defaults to `false`. Agent-written dishes stay `false`; the user sets `true` after checking the entry.
- A country dish with the same name as a Global Dish replaces it. Any other name or alias used twice stops the app at startup with a message naming both dishes and their files.
- Peanut is a fake Allergen: it goes only in `tests/packs/`, never in `packs/`.

After editing dishes, regenerate the list of dishes still to review in `docs/results/T2-unreviewed-known-dishes.md` (a test checks that it is current):

```sh
.venv/bin/python -m travel_companion.unreviewed_dishes
```

`POST /api/dish` with `{"name": "..."}` returns the dish card, or "Not in my guide. Ask staff." for a dish that isn't in the pack.

## Push-to-talk speech-to-text (whisper.cpp)

Hold **Hold to talk** on the home screen, ask in English, then let go. The browser records the mic as 16 kHz mono WAV and posts it to `POST /api/speech`. The app runs whisper.cpp's `whisper-cli` on the CPU (`-l en -ng`), so nothing leaves the machine, then sends the transcript through the same intent router as `POST /api/transcript` and shows the card it returns.

1. Install whisper.cpp:

   ```sh
   brew install whisper-cpp
   ```

2. Download the English base model (about 148 MB) into the gitignored `models/` folder. The script checks its SHA-256 and does nothing if the file is already there; `MODELS_DIR` works as for the llama.cpp model:

   ```sh
   scripts/fetch_whisper_model.sh
   ```

3. Start the app (`.venv/bin/travel-companion`) and open http://127.0.0.1:8765. The browser asks for mic access the first time. `[speech]` in `config/default.toml` sets `whisper_cli` and `whisper_model_path`; if either is missing the card says speech-to-text is not available.

To send a recording by hand:

```sh
say -o question.wav --file-format=WAVE --data-format=LEI16@16000 "show my allergy card"
curl -s http://127.0.0.1:8765/api/speech -H 'Content-Type: audio/wav' --data-binary @question.wav
```

The normal tests send text transcripts and a stand-in transcriber. The real-whisper test is skipped unless you point it at the model:

```sh
TRAVEL_COMPANION_REAL_WHISPER_MODEL=models/ggml-base.en.bin .venv/bin/pytest -q tests/test_real_whisper.py
```

The benchmark speaks sample questions with macOS `say` at run time, transcribes them and rewrites `docs/results/T6-speech-to-text.md`:

```sh
.venv/bin/python -m travel_companion.speech_benchmark --model models/ggml-base.en.bin
```
