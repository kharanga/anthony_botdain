# T3: OCR benchmark

Measured 2026-11-19 with `python -m travel_companion.ocr_benchmark`.
Photos: `specimens/photos` (3 with a transcription).
Allergen Terms: `packs/cr` (shellfish, 14 terms).

Character error rate is edit distance over the transcription length, with all whitespace collapsed to one space, so line breaks and column gaps do not count. The folded column ignores accents and case.
Term recall counts Allergen Term occurrences in the transcription (accents and case ignored) that are also in the OCR text. Accent-aware matching ignores case but needs the accents to match; accent-insensitive matching is what the app uses. A false positive is an occurrence in the OCR text beyond those in the transcription.
Colón signs kept counts ₡ that survive OCR. Seconds is the median per photo; the first photo includes model load.

## Per engine

| Engine | Photos | Character error rate | Folded character error rate | Term recall, accent-aware | False positives, accent-aware | Term recall, accent-insensitive | False positives, accent-insensitive | Colón signs kept | Seconds |
|---|---|---|---|---|---|---|---|---|---|
| tesseract | 3 | 2.9% | 2.9% | 6/6 (100%) | 0 | 6/6 (100%) | 0 | 0/12 | 0.13 |
| paddleocr | 3 | 3.1% | 3.1% | 6/6 (100%) | 0 | 6/6 (100%) | 0 | 0/12 | 2.58 |

## Per photo

| Engine | Photo | Character error rate | Missed, accent-aware | Missed, accent-insensitive | False positives, accent-insensitive | Unreadable |
|---|---|---|---|---|---|---|
| tesseract | `specimen-menu.png` | 3.6% | none | none | none |  |
| tesseract | `specimen-receipt.png` | 0.0% | none | none | none |  |
| tesseract | `specimen-seafood-menu.png` | 3.6% | none | none | none |  |
| paddleocr | `specimen-menu.png` | 3.6% | none | none | none |  |
| paddleocr | `specimen-receipt.png` | 0.0% | none | none | none |  |
| paddleocr | `specimen-seafood-menu.png` | 4.2% | none | none | none |  |

## OCR text

#### tesseract: `specimen-menu.png`

```text
SODA LA ESPECIMEN
Gallo pinto con huevo (2.500
Arroz con camarones (6.000
Ceviche de pescado (4.500
Plátanos maduros (1.500
Café con leche (1.200
Jugo de piña (1.800
```

#### tesseract: `specimen-receipt.png`

```text
SUPER ESPECIMEN S.A.
Factura 000123
Leche 1L 1.150
Pan cuadrado 1.600
TOTAL 2.750
```

#### tesseract: `specimen-seafood-menu.png`

```text
MARISCOS DE LA CASA
Sopa de camarón (5.500
CEVICHE MIXTO (4.800
Langostinos al ajillo 29.000
Arroz con jaiba 26.500
Pescado entero frito L7.000
Casado con pollo 23.800
```

#### paddleocr: `specimen-menu.png`

```text
SODA LA ESPECIMEN
Gallo pinto con huevo 2.500
Arroz con camarones 6.000
Ceviche de pescado 4.500
Plátanos maduros 1.500
Café con leche 1.200
Jugo de piña 1.800
```

#### paddleocr: `specimen-receipt.png`

```text
SUPER ESPECIMEN S.A.
Factura 000123
Leche 1L 1.150
Pan cuadrado 1.600
TOTAL 2.750
```

#### paddleocr: `specimen-seafood-menu.png`

```text
MARISCOS DE LA CASA
Sopa de camarón 5.500
CEVICHE MIXTO 4.800
Langostinos al ajillo9.000
Arroz con jaiba 6.500
Pescado entero frito 7.000
Casado con pollo 3.800
```

