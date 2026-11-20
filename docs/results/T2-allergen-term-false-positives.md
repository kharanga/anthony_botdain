# T2: Allergen Term false positives from accent- and case-insensitive matching

Measured 2026-11-19 with `python -m travel_companion.allergen_term_false_positives`.
Labelled specimen Menu Lines: `tests/fixtures/labelled_menu_lines.yaml` (46 lines, fake).

Matching folds accents and case and needs whole words (`paella` does not match `Paellera`).
A false positive is a line that names an Allergen Term but is labelled as not containing that Allergen.
Accent-only means the line would not have matched if accents were respected (case still ignored).

## Pack `packs/cr`

| Allergen | Lines that truly contain it | False positives | of which accent-only | Missed | Caught only because accents are ignored |
|---|---|---|---|---|---|
| shellfish | 14 | 2 | 0 | 0 | 1 |

### False positives

| Menu Line | Allergen | Matched terms | Truly contains |
|---|---|---|---|
| Bar El Cangrejo | shellfish | cangrejo | no |
| Restaurante Los Camarones | shellfish | camarones | no |

### Missed

None.

### Caught only because accents are ignored

| Menu Line | Allergen | Matched terms | Truly contains |
|---|---|---|---|
| CAMARON EMPANIZADO | shellfish | camarón | yes |

## Pack `tests/packs/specimen`

| Allergen | Lines that truly contain it | False positives | of which accent-only | Missed | Caught only because accents are ignored |
|---|---|---|---|---|---|
| shellfish | 14 | 2 | 0 | 0 | 1 |
| peanut | 8 | 2 | 1 | 1 | 2 |

### False positives

| Menu Line | Allergen | Matched terms | Truly contains |
|---|---|---|---|
| Bar El Cangrejo | shellfish | cangrejo | no |
| Restaurante Los Camarones | shellfish | camarones | no |
| Soda El Maní | peanut | maní | no |
| Pizza Mani Rosse | peanut | maní | no |

### Missed

| Menu Line | Allergen | Matched terms | Truly contains |
|---|---|---|---|
| Salsa de maníes tostados | peanut | none | yes |

### Caught only because accents are ignored

| Menu Line | Allergen | Matched terms | Truly contains |
|---|---|---|---|
| CAMARON EMPANIZADO | shellfish | camarón | yes |
| POLLO EN SALSA DE MANI | peanut | maní | yes |
| Galletas con mantequilla de mani | peanut | maní, mantequilla de maní | yes |

## Findings

- Ignoring accents added no shellfish false positives on this set. It caught one real line (`CAMARON EMPANIZADO`, written without the accent the way OCR and menu boards often do).
- Both shellfish false positives are restaurant names, which would match with accents respected too. They aren't caused by folding. T4 can rule them out by recognising header and name lines.
- Peanut (the fake Allergen) shows the one accent-only false positive, `Pizza Mani Rosse`: "mani" is a word in other languages. SPEC.md already accepts this for warnings. It costs an extra warning, never a missed one.
- Plurals have to be listed: `maníes` isn't matched because the fixture lists only `maní`. The `cr` shellfish list spells out every plural (camarones, langostas, langostinos, cangrejos, jaibas).
- Whole-word matching keeps `paella` from matching `Paellera` and `maní` from matching `Manicotti` and `Manito`.
- The set is 46 fake, hand-written lines. Re-measure on the real menu photos from T3.
