# travel-companion spec

Terms in **bold capitals** (Trip Build, Allergy Label, Photo Kind, …) are defined in `GLOSSARY.md`. Decisions with a recorded rationale are in `docs/adr/`.

## Product

An offline travel companion on a Raspberry Pi 5 (8 GB) with a 5" Touch Display 2, an AI HAT+ 2 (Hailo-10H), Camera Module 3, USB GPS and a USB mic. The user asks a question by holding a push-to-talk button or takes a photo, and every answer appears as a text card on screen. No spoken answers. It works with no internet or cell service. The project is separate from badminton-scout; only the Mac, SD card reader and power bank are shared.

The first Country Pack is Costa Rica (`packs/cr/`). Vietnam (`packs/vn/`) is second.

## Trip Build

The trip starts around 2026-12-02. Features in priority order:

1. Menu allergen scanner (shellfish)
2. Staff phrase card
3. Push-to-talk questions
4. Offline guide Q&A
5. Expenses
6. Document vault

Throughout the trip, Capture Mode saves real test data for the Backlog. If time runs short, features move from the bottom of this list to the Backlog.

Schedule: days 1–8 prototype on the Mac, using phone photos and the Mac mic. From about day 9, port to the Pi and test every feature with airplane mode on.

## Photos

Each photo goes through a router that proposes a Suggested Kind:

1. OCR runs on the photo.
2. Keyword rules check the text. Receipt clues: total, subtotal, IVA, factura, cédula jurídica, amounts in ₡ or $. Menu clues: several lines that each have a price and a food word.
3. If the rules aren't sure, the vision model (Qwen2-VL-2B on the HAT, the same model family on the Mac) picks exactly one kind.

The user then confirms the Suggested Kind, cycles through the kinds by hand (menu ↔ receipt ↔ ticket ↔ sign ↔ document ↔ other) and confirms one, or retakes the photo. When the router isn't sure, the cycle starts on menu. Nothing runs until a kind is confirmed. The confirmed kind is the Photo Kind. A spoken question that names the kind ("does this have shrimp?") sets the Photo Kind directly and skips the router. Every confirmation is saved together with the Suggested Kind, which builds the router's labelled test set.

The Photo Kind picks the handler:

- **menu** → menu allergen scanner (T4)
- **receipt** → expense entry (T9)
- **ticket** (bus or shuttle ticket, boarding pass, park entry) → document vault, with the full-brightness QR view (T8)
- **document** (passport, insurance, booking printout) → document vault (T8)
- **sign** (bus sign, timetable, landmark plaque) → Capture Mode only on the trip; the transit and landmark handlers are in the Backlog
- **other** → Capture Mode

Only menu photos are checked for Allergens.

## Menu result card

- Warnings go at the top: one Warning per Allergen on each line, strongest label first (e.g. "Contains shellfish: camarones").
- Ask staff lines show a grey "unknown dish — ask staff" note, with the staff phrase one tap away.
- Not typical lines show no marker at all.
- The summary always gives both counts, e.g. "No warnings in 12 known dishes. 4 unknown dishes — ask staff." It never shows a green check or anything like "all clear".
- On the trip, shellfish is the only active Allergen. Peanut exists only in test fixtures. Turning another Allergen on is a config change.

Every menu and receipt photo is saved for the test sets. Every saved photo carries its GPS position, time, Suggested Kind and Photo Kind.

## Expenses

- A receipt photo pre-fills an Expense for the user to confirm or edit: amount, currency, place, date and category.
- The currency defaults to the one printed on the receipt, with a one-tap toggle for paying a ₡ receipt in dollars.
- Category is one of food, transport, lodging, activities, shopping or other. The app suggests one from the receipt text ("soda" → food, "taxi" → transport), and the user confirms it.
- Spoken expenses ("I spent five mil on a taxi") pre-fill an Expense in the same way.

## Voice intents

The rules-first router handles exactly these:

1. Show the staff phrase ("show my allergy card")
2. Allergen question about the last menu scanned ("does the third one have shrimp?")
3. Guide question ("where can I see sloths near La Fortuna?")
4. Add an expense ("I spent five mil on a taxi")
5. Spending question ("how much have I spent on food?")
6. Open the vault ("show my boarding pass"), which still asks for the PIN

Anything else gets "I can't do that yet", plus a list of the six.

## Staff phrases

Trip Build phrases, all Machine-checked:

1. "I am allergic to shellfish: shrimp, lobster, crab. Mollusks are OK."
2. "Does this dish contain shrimp, lobster, crab, or seafood broth?"
3. "Where is the nearest hospital / pharmacy?"

## Guide answers

A guide answer is the top 2–3 Wikivoyage passages found by keyword search over the ZIM file, plus a 1–2 sentence LLM summary drawn only from those passages. The card shows the passage text and the article name as its evidence. With no match, it says "not in my guide".

## Home screen

- The arcade button is push-to-talk only.
- The home screen has six large tiles: Scan (camera, then router, then confirm), Allergy card, Guide, Expenses, Vault and Back up.

## Backup

Back up writes an encrypted copy of the data folder to a USB stick: expenses, captured photos, router labels and the vault, which stays encrypted under the PIN. Run it each evening on the trip.

## Trip Build ready

The Trip Build is ready when all of these are true:

1. Every Trip Build feature passes on the Pi with airplane mode on.
2. The menu allergen scanner reaches ≥95% recall on crustacean dishes in the specimen set.
3. The device runs ≥4 hours of mixed use on the power bank with `vcgencmd get_throttled` = 0.
4. A backup has been restored successfully at least once.

## Milestones

Each milestone writes its results to `docs/results/`.

| # | Task | Depends on | Delivers |
|---|------|-----------|----------|
| T1 | Skeleton + config | — | Config (allergen=shellfish, country=cr, home currency=USD, Rate), DuckDB, answer card structure, local UI shell |
| T2 | Costa Rica pack v0 | T1 | Allergen Terms (shellfish real, peanut fake), ~150 Known Dishes, Phrases (Machine-checked), CRC + USD, time zone, guide, transit, landmarks; schema and term-matching tests |
| T3 | Spanish OCR | T1 | Tesseract `spa` vs. PaddleOCR (plus the HAT vision model on the Pi) on 30+ real photos; accent-aware and accent-insensitive matching; false positives measured |
| T4 | Menu allergen scanner | T2, T3, T5 | Matches each Menu Line to a Known Dish (aliases, accent- and case-insensitive, OCR-typo tolerant; extra ingredient words on the line are added to the dish's Ingredients; a weak match counts as no match). Gives each line one Allergy Label per active Allergen. A Warning shows only for Contains and Often contains, naming the Allergen and the Ingredient or Allergen Term behind it. ≥95% recall on crustacean dishes |
| T5 | Local LLM + guardrails | T1 | Model endpoint (ADR 0001); speed, memory and quality on Mac and Pi; tests that facts aren't altered |
| T6 | Voice + intent router | T1, T5 | whisper.cpp, rules-first router; 50 sample questions; latency measured |
| T8 | Encrypted document vault | T1 | 6-digit PIN, auto-lock after 2 min, full-brightness QR/barcode view; specimen documents in the repo, real ones only in the data dir |
| T9 | Expense tracker | T3, T5 | Receipt OCR; ₡ and USD parsing ("₡5.000", "5 mil", "5 rojos"); read-only natural-language-to-SQL with the SQL shown |
| T10 | Offline travel Q&A | T2, T5 | Wikivoyage Costa Rica via Kiwix; answers only from sources, otherwise "not in my guide" |
| T17 | Photo router | T3, T5, T11 | Suggested Kind for every photo, plus the confirm / cycle / retake flow; ≥95% of suggestions match the confirmed kind on the labelled set; menus suggested as something else counted separately |
| T11 | Vision runtime on the HAT | T5 | Qwen2-VL-2B through `hailo-ollama`; the Mac equivalent; HAT vs. CPU latency, watts and quality; serves the photo router |
| T14 | Touch-screen UI | T4, T6, T8–T10, T17 | Home screen with six tiles, answer cards, large touch targets, dark theme, idle dimming |
| T18 | Backup | T8, T9 | Encrypted copy of the data folder to a USB stick, plus a restore that has been tested |
| T15 | Pi port + measurements | T14, T18 | Every feature tested with airplane mode on; latency and power per feature; battery hours |
| T16 | Ship | T15 | README, demo video, results, attributions; a fresh clone runs on the Mac with fake data; post-trip spec written from the Backlog and the captured data |

## Backlog

Each item gets a spec of its own after the trip, built on the data Capture Mode collected.

| # | Task | Depends on | Delivers | Needs from Capture Mode |
|---|------|-----------|----------|-------------------------|
| T7 | Itinerary + "What's next?" | T1, T5 | The correct next item across time zones and midnight, linked to its ticket. Stretch: importing booking photos | — |
| T12 | Transit helper | T2, T3, T6, T11 | Bus signs, timetables, shuttle tickets, commuter train (no metro); 0 invented stop names | Bus and shuttle sign photos, timetables |
| T13 | Landmark guide | T2, T5, GPS | GPS candidates plus image match (volcanoes, parks, beaches); top-1 and top-3 accuracy; an image license recorded for each reference image | Landmark photos with GPS |

Not planned: spoken answers, pronunciation coach, general translation, cloud sync. Optional idea: an AR overlay on the Pi 5 GPU.

## Costa Rica pack notes

- **Shellfish terms** (crustaceans): camarón/camarones, langosta, langostino, cangrejo, jaiba. Mixed-seafood words count as Allergen Terms: mariscos, frutos del mar, ceviche mixto, paella. Mollusk-only words (calamar, pulpo, almeja, mejillón, chucheca, piangua) are not Allergen Terms, so those lines get Ask staff unless they match a Known Dish. Ceviche de pescado is a Known Dish marked Often contains.
- **Peanut terms** (fake allergen, for tests): maní (the main Costa Rican word), cacahuate/cacahuete, mantequilla de maní, aceite de maní. Accent-insensitive "mani" is fine for warnings, but measure false positives. Peanut hides in sweets, sauces and snacks (maní garapiñado, cajeta de maní).
- **Known Dishes**: about 150, built on the Mac before the trip from Wikipedia's Costa Rican cuisine articles, Wikibooks Cookbook and the Wikivoyage "Eat" sections. An LLM helps extract the Ingredients, the user reviews every entry, and each entry records its source. On the device, a dish that isn't in the pack gets Ask staff; there's no on-device ingredient guessing. Weighting: sodas (casado, gallo pinto, olla de carne, chifrijo), coastal and Caribbean food (rice and beans, rondón, ceviche, arroz con mariscos), and generic restaurant dishes (pasta, pizza, burgers, sushi, fajitas), where shrimp hides without being named.
- **Phrases**: all Machine-checked. Carry a printed allergy card as a backup.
- **Money**: colón (CRC, ₡), with prices written like "₡5.000" and "5 mil"; the slang "rojo" means ₡1,000. US dollars are widely accepted. Each Expense stores its amount in the currency actually paid. Home currency is USD, and the Rate is colones per dollar, set before the flight and editable on the device.
- **Time zone**: America/Costa_Rica (UTC−6, no daylight saving time).
- **Guide**: Wikivoyage Costa Rica as a Kiwix ZIM file (CC BY-SA, attribution required).
- **Why offline**: rainforest, beach and mountain areas often have no service.

## Hardware

All bought. The device: Raspberry Pi 5 8 GB, Active Cooler, 27W power supply, Touch Display 2 5", 128 GB A2 microSD, Camera Module 3 with a 200 mm Pi 5 cable, Mini USB Microphone, 30 mm arcade button with LED wired to GPIO, Pi 5 RTC battery, Ultimate GPS over USB, AI HAT+ 2.

Power: the Pi 5 wants 5V/5A. Pick a power bank by its 5V output, not its total watts; a 5V/3A bank works but limits USB power. Check `vcgencmd get_throttled` under load.

## Risks

1. Quality of Spanish OCR from the HAT vision model after Hailo quantization is untested (T3, T11).
2. Phrases are only Machine-checked.
3. Case fit for the cooler, AI HAT+ 2 and display (candidate case: Waveshare PI5-CASE-TD2-5inch).
4. Battery life of the full stack is unmeasured until T15.
5. Landmark reference image licenses (Backlog, T13).
