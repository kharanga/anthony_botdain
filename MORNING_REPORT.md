# Morning report — overnight run, 2026-11-18 → 19

Everything landed on **`trip-build-integration`**, and that branch is pushed. `main` is untouched. PR #29 is open against `main`, ready for review, and says it closes #20–#28; merging it is up to you.

**Tests: 89 passed, 2 skipped** (`.venv/bin/pytest -q`).

## Tickets landed (9 of 9)

| Ticket | What it does now |
|---|---|
| #20 App boots and returns an answer card | FastAPI app on port 8765; default config with cr, shellfish, USD and Rate; answer card with evidence; dark UI shell; HTTP-API test harness |
| #21 Edit the Rate on the device | DuckDB in `data/`; `GET`/`PUT /api/rate`; Rate form in the UI; survives a restart |
| #22 Model endpoint with a fake server | `POST /api/ask` through one OpenAI-compatible endpoint (ADR 0001); 503 `model_unavailable` card; reusable scripted fake server; prompts trimmed to 2,048 tokens (estimated, cautious) |
| #23 Fact guardrail | Rejects model replies that drop, change or add facts, and falls back to a template answer; demo route `POST /api/ask/rate` |
| #24 Real llama.cpp on the Mac | `scripts/fetch_model.sh` and `scripts/start_model_server.sh`; Qwen2.5-1.5B Q4_K_M in the gitignored `models/`; opt-in real-model tests |
| #25 Mac model benchmark | `python -m travel_companion.model_benchmark`; results in `docs/results/T5-mac-model-benchmark.md` |
| #26 Add and unlock a document | 6-digit PIN; AES-GCM with an scrypt key; documents encrypted in DuckDB; locked returns nothing; `/vault` page |
| #27 Vault auto-lock | Locks after 2 minutes with no use, with an injectable clock; lock checks don't count as use; UI returns to the PIN screen |
| #28 Full-brightness ticket view | Full-screen page; brightness backend set by config (records on Mac and in tests, sysfs on the Pi); brightness restored on close or lock |

Benchmark highlights (M2, 8 GB): about 66 tokens/s, first token in 0.09–0.13 s for short prompts and 1.0 s near the 2,048-token limit, about 1.2 GB peak memory, model loads in 1.4 s. The guardrail rejected 16 of 108 real replies (15%). Most of those were real errors, such as a wrong conversion or an invented currency; some rejections were stricter than needed, and in those cases the card shows the correct template answer.

## Tickets skipped

None. No ticket was blocked or unclear.

## Code review (one pass at high effort) → one fix pass → focused checks

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | Guardrail accepted an inverted Rate ("one colón = 510 dollars") | important | **Fixed.** Checked with 7 accepted and 4 rejected phrasings |
| 2 | Close could race the open request, leaving brightness at max | important | **Fixed, with a gap left.** If the tab closes while the open request is still pending, the race remains; the next lock or vault page load cleans it up |
| 3 | Null or non-text model content gave a 500 | important | **Fixed** |
| 4 | `export_tasks.py` crashed on an empty body or a title with no colon | important | **Fixed** |
| 5 | Every 422 in the vault UI said "Enter exactly 6 digits" | nit | **Fixed.** No test, because it's page JavaScript |
| 6 | One failed case aborted the whole benchmark run | nit | **Fixed.** Failures are recorded and the run continues. Partial results aren't saved if the run crashes |
| 7 | Polls decrypted every vault photo | nit | **Fixed.** Labels are sealed separately. No test proves a poll skips decryption, because that isn't visible over HTTP |
| 8 | A 404 for one document closed another document's full-screen view | nit | **Fixed** |
| 9 | Unlimited wrong-PIN attempts; PIN setup race | nit | **Partly fixed.** After 5 wrong PINs there's a wait (30 s, doubling, up to 1 h), and setup and unlock are serialized. Still open: the attempt count resets on restart, and the key-derivation cost and PIN length are unchanged. A 6-digit PIN can still be brute-forced offline by anyone holding the `data/` folder |
| 10 | SVG photos could run script | nit | **Fixed.** Only raster image types are accepted, and photos are sent with `nosniff` and a sandbox CSP |

## Still open / worth your attention

- **#2 gap:** closing the tab while the open request is pending can still leave the backlight at max until the next lock or vault page load.
- **#9 offline brute force:** a longer passcode or a higher scrypt cost would make the vault much harder to crack. That's your call.
- **Guardrail side effects:** "510 Costa Rican colones" is wrongly rejected; this is harmless, because the template answer is used. "One colón buys ₡510 in dollars." still gets through.
- **₡ thousands separator:** the guardrail reads "₡5.000" as 5. Fix this before expense answers go through it (T9).
- **`model` field:** llama-server doesn't need one. The Pi's `hailo-ollama` probably does (T11).
- **Temperature:** none is set, so the guardrail rejection rate varies between runs (8–19% on single passes).
- **Pi brightness:** writing to `/sys/class/backlight` may need permissions on the Pi (T15).
- **Starlette warning:** the test client prints an httpx deprecation warning. It's harmless.

## Tests skipped

- **2 real-model tests** in `tests/test_real_model.py`. They're skipped unless `TRAVEL_COMPANION_REAL_MODEL_URL` is set. They were run once against a real llama-server and passed.
- **Never run in a real browser:** the UI shell, the Rate form, the vault page, the full-screen page and the 422-message fix. All of them were checked only through the HTTP API.

## Housekeeping

- All implementer worktrees are removed. Their merged branches are deleted locally; they were never pushed.
- `docs/task/` hasn't been refreshed for ticket status, because the tickets close when PR #29 merges. After merging, run `python3 scripts/export_tasks.py docs/task docs/archived` and commit the result.
- To run the app: `.venv/bin/python -m travel_companion`, then open http://127.0.0.1:8765.
