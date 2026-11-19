# #3: T2: Costa Rica Country Pack v0

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/3

Part of #1.

## What to build

The Country Pack loader and the `cr` pack:
- Allergen Terms per Allergen. Shellfish (crustaceans): camarón/camarones, langosta, langostino, cangrejo, jaiba, plus mixed-seafood words mariscos, frutos del mar, ceviche mixto, paella. Mollusk-only words are not shellfish Allergen Terms. Peanut is a fake Allergen used only in specimen data.
- About 150 Known Dishes, each with aliases, Ingredients marked usual or sometimes, and a recorded source. Built on the Mac from Wikipedia's Costa Rican cuisine articles, Wikibooks Cookbook and the Wikivoyage "Eat" sections. An LLM helps extract the Ingredients, and the user reviews every entry. Weighted toward sodas, coastal and Caribbean food, and generic restaurant dishes.
- Phrases, all Machine-checked: (1) "I am allergic to shellfish: shrimp, lobster, crab. Mollusks are OK." (2) "Does this dish contain shrimp, lobster, crab, or seafood broth?" (3) "Where is the nearest hospital / pharmacy?"
- CRC + USD, America/Costa_Rica time zone, the Wikivoyage ZIM reference

## Blocked by

#2 (T1)

## Done when

- Pack schema is validated by tests
- Term matching ignores accents and case, with false positives measured
- Every Known Dish has a source
- Specimen peanut data is present only in test fixtures

## User stories

33–38 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
