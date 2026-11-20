# Morning report — T2, T3 and T6 run, 2026-11-19

Everything landed on **`pack-ocr-voice-integration`**, and that branch is pushed. `main` is untouched. PR #42 is open against `main`, ready for review, and closes #30–#36 and #38–#41; merging it is up to you.

**Tests: 280 passed, 4 skipped** (`.venv/bin/pytest -q`).

## Tickets landed (11 of 11)

| Ticket | What it does now |
|---|---|
| #30 YAML Country Pack loader and Allergen Term matching | `packs/cr/` in YAML, checked against a schema at startup (a broken pack stops the app and names the file). `POST /api/menu-line` returns the matched Allergen Terms. One shared accent- and case-folding function. Peanut exists only in `tests/packs/specimen/` |
| #31 Staff phrase card | The three Phrases in `packs/cr/phrases.yaml`, each marked Machine-checked. `GET /api/staff-phrase`. An "Allergy card" button opens a full-screen large-text view |
| #32 Known Dish YAML | `packs/global/dishes.yaml` plus `packs/cr/dishes.yaml`, merged at load, with a country dish replacing a Global Dish that shares a name or alias. `POST /api/dish` returns the Ingredients and source, and says "unreviewed" until `reviewed: true` |
| #33 Global Dishes | **56** dishes, each with a source, all unreviewed |
| #34 Costa Rica dishes | **113** dishes, mostly soda plates and coastal and Caribbean food, each with a source, all unreviewed. Ceviche de pescado lists shrimp as a sometimes Ingredient; mollusk-only dishes have no shellfish Ingredient |
| #35 OCR with confidence | `POST /api/photo` returns the OCR lines from Tesseract `spa`, each with a confidence; lines below 70 are flagged Ask staff. The OCR engine can be swapped in config. Specimen photos are fake renders |
| #36 OCR benchmark | `python -m travel_companion.ocr_benchmark`, comparing Tesseract and PaddleOCR (PaddleOCR is an optional extra, `.[paddleocr]`). The README explains the photo and transcription format for #37 |
| #38 Rules-first intent router | `POST /api/transcript` picks one of the six intents and pulls out its details, or says "I can't do that yet" plus the list. All 50 sample questions route correctly; routing takes about 20 µs |
| #39 Model fallback | When no rule matches, the model picks one of the six labels or none. A bad label or a model that is down gives "I can't do that yet", never an error |
| #40 "Show my allergy card" | Typed or spoken, it opens the staff phrase card. The UI shell has a typed transcript form |
| #41 Push-to-talk speech | `POST /api/speech` runs whisper.cpp (base.en) on the CPU, and a "Hold to talk" button sends the Mac mic. `scripts/fetch_whisper_model.sh` downloads the model and checks its SHA-256 |

**Results** in `docs/results/`:
- **Allergen Term false positives:** ignoring accents added no shellfish false positives (`T2-allergen-term-false-positives.md`).
- **OCR:** on the fake specimen photos, both engines get about 3% character error rate and find 6 of 6 Allergen Terms with every accent kept. Tesseract takes 0.13 s per page, PaddleOCR 2.6 s (`T3-ocr-engine-comparison.md`).
- **Speech-to-text:** 8.3% word error rate. 9 of 12 spoken samples route the same as the typed question, with a median of about 1.4 s. All three misses are Spanish words: ceviche, La Fortuna, colones (`T6-speech-to-text.md`).

## Tickets skipped

- **#37** was skipped as you asked. It needs your 30+ real photos and their transcriptions, and nothing is waiting on it except the engine choice.
- Nothing else was blocked or unclear.

## Code review (one pass at high effort) → one fix pass → focused checks

I checked each fix by sending the exact failing phrase through the API again.

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | "3 thousand five hundred colones" was read as 3000 | important | **Fixed.** Now 3500 |
| 2 | "add one coffee for 2000 colones" was read as 1 | important | **Fixed.** Now 2000 CRC. An amount next to a currency or multiplier wins |
| 3 | "a hundred dollars" wasn't recognised as an amount | important | **Fixed.** Now 100 USD |
| 4 | "Is it safe to eat seafood in Puntarenas?" was treated as a question about the last menu | important | **Fixed.** Now a guide question; "does it have shrimp" still asks about the menu |
| 5 | "this dish" was read as a dish name | important | **Fixed.** It now means the current menu item |
| 6 | With no OCR engine installed, `/api/photo` returned a bare 500 | important | **Fixed.** Now a 503 card saying no OCR engine is installed |
| 7 | The menu-line card had no Allergy Label, and "No Allergen Terms on this line." read like an all-clear | nit | **Partly fixed.** It now says Contains or Ask staff and carries the staff phrase action. Not typical has to wait for T4, which matches lines to Known Dishes |
| 8 | A corrupt whisper download was never fetched again | nit | **Fixed.** The checksum is checked before the file is moved into place |
| 9 | Non-speech markers like "[Music]" or "(wind blowing)" were routed as questions | nit | **Fixed.** Any text in brackets or parentheses is stripped |
| 10 | A country dish alias matching a Global Dish name stopped the app at startup | nit | **Fixed.** The country dish now replaces the Global Dish |

## Still open / worth your attention

- **Review the dishes:** all 169 are unreviewed, and the list is in `docs/results/T2-unreviewed-known-dishes.md`. Agents flagged these to check first:
  - **Pad thai:** peanut is left out, because peanut can't appear in `packs/`.
  - **Shrimp without a source:** risotto, ravioli (lobster), teriyaki, quesadilla, poke and ramen list `shrimp: sometimes`, which their Wikipedia pages don't state. That follows the "prefer sometimes when unsure" rule.
  - **Marinara:** "spaghetti marinara" and "pasta marinera" are aliases of Seafood pasta, which is right in Spain but in the US means tomato sauce.
  - **Translations:** the phrase translations are Claude's own. The allergy phrase says "crustáceos" rather than "mariscos", because mariscos includes mollusks.
- **The ₡ sign is never read:** both OCR engines miss it, so "₡9.000" can come out as "29.000" or "9.000". T9 (expenses) must handle this, and so must T4 for prices.
- **OCR engine not chosen:** that's #37's job.
- **The router's word lists are fixed in code:** expense categories and allergen words aren't read from the Country Pack yet.
- **Wording of the unknown-dish card:** `POST /api/dish` answers a dish that isn't in the pack with "Not in my guide. Ask staff." The "not in my guide" wording is meant for guide answers, so this might be worth rewording.
- **The menu-line card says "no Allergen Term or Known Dish"**, but that endpoint doesn't look up Known Dishes yet; T4 adds that.
- **Two bare numbers:** "add two coffees for 3000" picks 3000 only because "colones" follows it. Two bare numbers with no currency still take the first one.
- **Spanish words in speech:** whisper base.en mishears them. A larger model, or a prompt listing words from the pack, could help. This belongs to T6 or T15.
- **The T2 issue (#3) still says you review every dish entry.** The tickets and `SPEC.md` describe the new "unreviewed until you mark it" flow.
- **GPIO arcade button:** not ticketed; it waits for the Pi, as you asked.
- **An agent mistake:** while testing #41, an agent killed a local Python `http.server` on port 8799 that no other agent owned. If you had something running on that port, restart it.
- **Starlette warning:** the test client still prints an httpx deprecation warning. It's harmless.

## Tests skipped

- **4 opt-in tests**, skipped unless their environment variable is set:
  - **2 real-model tests** (`TRAVEL_COMPANION_REAL_MODEL_URL`): not run in this pass.
  - **The real-whisper test** (`TRAVEL_COMPANION_REAL_WHISPER_MODEL`): run once against the real model by the #41 agent, and it passed.
  - **The PaddleOCR test** (`TRAVEL_COMPANION_PADDLEOCR=1`): run once by the #36 agent, and it passed.
- **Never run in a real browser:** the full-screen phrase view, the typed transcript form and the "Hold to talk" mic recording. They were checked only through the HTTP API, plus a live curl with a WAV made by `say` for speech.

## Housekeeping

- **Worktrees:** all implementer worktrees are removed, and their merged branches are deleted locally; they were never pushed.
- **Models:** the whisper model is in the gitignored `models/` folder, next to the Qwen model.
- **Spanish OCR data:** I installed `tesseract-lang` with Homebrew.
- **After you merge PR #42:**
  - **T2 (#3):** every ticket is closed, so close the issue after checking it.
  - **T3 (#4):** stays open for #37.
  - **T6 (#7):** still describes the GPIO button, so close it or ticket the button for later.
  - **Then** run `python3 scripts/export_tasks.py docs/task docs/archived` and commit the result.
