# T3: OCR lines with confidence (#35)

Run on 2026-11-19 on the Mac (arm64, Darwin 27.2.0, Python 3.13.2) with Tesseract 5.5.0 (leptonica 1.85.0), language `spa` from Homebrew `tesseract-lang`, default page segmentation.

## Method

`scripts/render_specimen_photos.py` renders two fake pages with Pillow (Arial 40 px, black on white, 1000 px wide) into `specimens/photos/`. Each was sent to `POST /api/photo`. A line's confidence is the lowest word confidence Tesseract gives on that line, so one unclear word is enough to flag the line. The default threshold is 70 (`[ocr] low_confidence_threshold`).

## Specimen menu (`specimen-menu.png`)

| Rendered line | OCR line | Confidence | Flagged |
|---|---|---|---|
| SODA LA ESPECIMEN | SODA LA ESPECIMEN | 91.9 | no |
| Gallo pinto con huevo  ₡2.500 | Gallo pinto con huevo (2.500 | 69.0 | yes |
| Arroz con camarones  ₡6.000 | Arroz con camarones (6.000 | 58.6 | yes |
| Ceviche de pescado  ₡4.500 | Ceviche de pescado (4.500 | 76.8 | no |
| Plátanos maduros  ₡1.500 | Plátanos maduros (1.500 | 81.6 | no |
| Café con leche  ₡1.200 | Café con leche (1.200 | 84.8 | no |
| Jugo de piña  ₡1.800 | Jugo de piña (1.800 | 85.2 | no |

## Specimen receipt (`specimen-receipt.png`)

| Rendered line | OCR line | Confidence | Flagged |
|---|---|---|---|
| SUPER ESPECIMEN S.A. | SUPER ESPECIMEN S.A. | 92.5 | no |
| Factura 000123 | Factura 000123 | 96.1 | no |
| Leche 1L  1.150 | Leche 1L 1.150 | 92.5 | no |
| Pan cuadrado  1.600 | Pan cuadrado 1.600 | 96.0 | no |
| TOTAL  2.750 | TOTAL 2.750 | 95.7 | no |

## Findings

- Accented Spanish (á, é, ñ) came back exactly on every line.
- Tesseract `spa` reads the colón sign ₡ as `(` on every menu price. The misread word carries the lowest confidence on its line, which pulled two lines under 70. Expense parsing (T9) cannot rely on ₡ surviving OCR; a `(` directly before a number is likely a colón sign.
- These are clean renders, not phone photos. The 30+ real photo benchmark against PaddleOCR is #36.
