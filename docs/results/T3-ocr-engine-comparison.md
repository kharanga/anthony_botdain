# T3: OCR engine comparison on the specimen set (#36)

Run on 2026-11-19 on the Mac (Apple M2, 8 GB, Darwin 27.2.0, Python 3.13.2). The generated numbers are in `T3-ocr-benchmark-specimen.md`, written by `python -m travel_companion.ocr_benchmark --include-ocr-text`.

## Engines

- Tesseract 5.5.0 (leptonica 1.85.0), language `spa` from Homebrew `tesseract-lang`.
- PaddleOCR 3.7.0 on paddlepaddle 3.3.1 (CPU), language `es`, models PP-OCRv6_medium_det and PP-OCRv6_medium_rec. Document orientation, unwarping and text-line orientation are off.

PaddleOCR installs from pip wheels on Apple Silicon with Python 3.13 and runs. It is the optional extra `paddleocr` in `pyproject.toml`, not a core dependency. Its first run downloads about 130 MB of models into `~/.paddlex/official_models/`; after that it runs offline. The engine sets `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK` so it does not check the model host at start-up. Whether it installs on the Pi 5 is not tested here.

## Specimen set

Three fake pages rendered by `scripts/render_specimen_photos.py`, each with a `.txt` transcription: the clean menu and receipt from #35, and `specimen-seafood-menu.png`, a seafood menu made to look more like a phone photo (grey on grey, tilted 1.5°, blurred, scaled to 60%). It has 6 shellfish Allergen Term occurrences across the set, including `camarón` with an accent and `CEVICHE MIXTO` in capitals.

## Findings

- Both engines found all 6 Allergen Terms, with no false positives, under both accent-aware and accent-insensitive matching. Both kept every accent, so on this set the two matching modes do not differ. Clean renders are too easy to decide this; the 30+ real photos in #37 are what will decide it.
- Character error rate is about 3% for both engines, and nearly all of it is the colón sign.
- **Neither engine keeps ₡ (0 of 12).**
  - Tesseract reads ₡ as `(` on the clean menu (as #35 found: `Arroz con camarones (6.000`). On the degraded seafood menu it reads ₡ as `2` or `L` (`Langostinos al ajillo 29.000`, `Pescado entero frito L7.000`). ₡9.000 read as 29.000 is a wrong price that looks right, so expense parsing (T9) must not trust a leading digit that might be a misread ₡.
  - PaddleOCR drops ₡ entirely (`Arroz con camarones 6.000`). It once glued the price onto the dish (`Langostinos al ajillo9.000`).
- Speed: Tesseract takes a median 0.13 s per page. PaddleOCR takes a median 2.6 s, and its first page also loads the models (about 12 s on a cold start).
- No engine is chosen yet. Pick one only after #37 runs the benchmark on real photos.
