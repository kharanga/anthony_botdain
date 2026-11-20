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

## OCR benchmark: Tesseract vs PaddleOCR

Tesseract is the default engine (`[ocr] engine = "tesseract"`). PaddleOCR is an optional extra, not a core dependency:

```sh
.venv/bin/pip install -e '.[dev,paddleocr]'
```

The first PaddleOCR run downloads its models (about 130 MB) into `~/.paddlex/official_models/`, so run it once while online. After that it works offline. Set `[ocr] engine = "paddleocr"` to use it in the app. Its real-engine test is skipped unless you ask for it:

```sh
TRAVEL_COMPANION_PADDLEOCR=1 .venv/bin/pytest -q tests/test_paddleocr_engine.py
```

Run the benchmark on the specimen photos:

```sh
.venv/bin/python -m travel_companion.ocr_benchmark --include-ocr-text
```

It runs every engine in `travel_companion.ocr` (`--engines tesseract` for one) over each photo in `--photos` (default `specimens/photos/`) that has a transcription, and writes `docs/results/T3-ocr-benchmark-specimen.md` (`--results` to change it). It reports character error rate, Allergen Term recall and false positives for accent-aware and accent-insensitive matching, how many colón signs (₡) survive, and seconds per photo. An engine that is not installed is listed as not measured. To rebuild the specimen photos and their transcriptions, run `.venv/bin/python scripts/render_specimen_photos.py`.

### Real photos

Real photos stay in the gitignored `data/` folder, never in the repo. Put them in `data/ocr-benchmark/` and run:

```sh
.venv/bin/python -m travel_companion.ocr_benchmark --photos data/ocr-benchmark --results docs/results/T3-ocr-benchmark-real-photos.md
```

Leave out `--include-ocr-text` for real photos: without it, the results file holds only photo file names, scores and pack Allergen Terms, never the text read from a photo. Check the file before you commit it, and give photos names that say nothing private (`menu-01.jpg`, `receipt-07.jpg`).

### Transcription format

Each photo needs a transcription next to it with the same name and a `.txt` extension:

```text
data/ocr-benchmark/menu-01.jpg
data/ocr-benchmark/menu-01.txt
```

- Photos: `.jpg`, `.jpeg`, `.png`, `.tif` or `.tiff`. Export iPhone HEIC photos as JPEG first. A photo without a `.txt` is listed as skipped.
- The `.txt` is plain UTF-8 text: type the text exactly as printed, one printed line per line, top to bottom and left to right.
- Keep accents, `ñ` and case as printed. If the menu prints `CAMARON` without an accent, type it without one. Do not fix spelling.
- Type the colón sign as `₡` (U+20A1; on a Mac, paste it). Keep prices as printed, for example `₡4.500`.
- Spacing does not matter: runs of spaces, tabs and line breaks all count as one space, so a dish and its price on one row can be typed `Ceviche mixto  ₡4.800`.
- Type every line you can read, including headings, prices and footers. Leave out only text you cannot read yourself.
- Character error rate compares the whole transcription with the whole OCR text, so a line left out of the transcription counts as an error for any engine that reads it. Allergen Term recall uses the terms in the transcription as the truth, so every shellfish word on the page must be typed.
