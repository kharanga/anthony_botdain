# travel-companion

An offline travel companion: a Raspberry Pi 5 (8 GB) with a 5" Touch Display 2 and an AI HAT+ 2 (Hailo-10H). The user asks by push-to-talk voice and gets the answer as a text card on screen. It works with no internet or cell service. The first country pack is Costa Rica (`packs/cr/`); Vietnam (`packs/vn/`) comes second. The app loads one pack, chosen in config.

The plan is in `SPEC.md`: Trip Build, photo routing, milestones and their dependencies, the Backlog, Costa Rica pack notes, hardware and risks. Read it before starting or scoping any milestone. Project terms are defined in `GLOSSARY.md`.

## Timeline

The trip starts around 2026-12-02. All hardware has been bought. Build the Trip Build in the priority order given in `SPEC.md`, and start the Pi port by about day 9. If time runs short, the lowest-priority features move to the Backlog; they are never deleted.

## Stack

- Python backend on FastAPI with a local web UI. On the Mac it runs in a browser tab; on the Pi it runs in Chromium kiosk mode. The same UI code serves both.
- DuckDB for data. The Costa Rica pack lives in `packs/cr/`.
- Models sit behind one OpenAI-compatible model endpoint set in config (see `docs/adr/0001-one-model-endpoint.md`). On the Mac it's the llama.cpp server running Qwen2.5-1.5B (GGUF, Q4_K_M). On the Pi it's `hailo-ollama` running Qwen2.5-1.5B and Qwen2-VL-2B on the HAT.
- Speech-to-text is whisper.cpp on the CPU, on both Mac and Pi. Speech input is English only.
- OCR: Tesseract `spa` vs. PaddleOCR, decided by measurement in T3.

## AI HAT+ 2 (Hailo-10H)

- Install `dkms hailo-h10-all`. `hailo-all` is the package for older Hailo chips, and the two conflict.
- Use the pre-compiled `.hef` models from the Hailo GenAI Model Zoo. Compiling your own model needs x86 Linux, and full LLMs aren't officially supported. Vision models: Qwen2-VL-2B (fastest), Qwen3-VL-2B, Qwen3-VL-4B. The zoo also has small LLMs (Qwen2.5-1.5B, Qwen3-1.7B/4B, Llama3.2-1B) and Whisper Tiny through Medium.
- Every model on the HAT has a 2048-token context. Size prompts and retrieved passages to fit.
- Two ways to run them: `hailo-ollama`, an Ollama-compatible REST server on :8000 that also accepts `/v1/chat/completions`, or the Python API `hailo_platform.genai` (`LLM`, `VLM`, `Speech2Text`).
- Hailo's own speed figures (e.g. Qwen2-VL-2B ≈ 1 s to the first token, about 7 tok/s) aren't confirmed as Pi 5 numbers. Measure them in T11.
- Spanish OCR quality of the vision models after Hailo quantization is untested. Benchmark it against Tesseract before relying on it.

## Design rules

- **Facts come from data.** Prices, terms, phrases, stops and times are read from the pack or from the user's own records. The LLM only routes and phrases answers; tests check that it never changes a fact.
- **Every card shows its evidence**: the OCR line, pack entry or guide passage behind the answer.
- **Cheapest step first**: try a keyword match or lookup before any model call.
- **Allergy answers are labelled** *Contains*, *Often contains*, *Ask staff* or *Not typical*, and the staff phrase is always one tap away. The word "safe" never appears in allergy output. Low-confidence OCR lines get *Ask staff*.
- **Offline and private**: no network calls at runtime, and documents are encrypted (T8).
- **Ask on 0 matches**: when the guide has no answer, the card says "not in my guide".

## Allergens

- The trip build uses **shellfish**, the user's real allergy (not severe), as the active allergen. Shellfish means crustaceans only.
- Peanut is a **fake** allergen used for the specimen data and tests. The code supports more than one allergen.
- Allergy Labels follow the rules in `GLOSSARY.md`. Not typical requires a match to a Known Dish; an unrecognized line gets Ask staff.
- Every phrase in the Trip Build is Machine-checked (Google Translate or Claude). Show that status on the phrase card.

## Repo

- This repo is public. Commit only fake or specimen data: menus, receipts, documents and itineraries.
- Real trip data (vault documents, photos, expenses) goes in a gitignored data directory.
- Every milestone writes its measurements to `docs/results/`.
- A fresh clone has to run on the Mac with fake data alone.
