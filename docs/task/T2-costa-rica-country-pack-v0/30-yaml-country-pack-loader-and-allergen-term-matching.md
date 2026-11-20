# #30: YAML Country Pack loader and Allergen Term matching

**Parent:** #3  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/30

## Parent

#3

## What to build

The app loads the Country Pack chosen in config from YAML files, so adding or removing an Allergen Term means editing YAML only. The `cr` pack holds the shellfish Allergen Terms (crustaceans: camarón/camarones, langosta, langostino, cangrejo, jaiba, plus the mixed-seafood words mariscos, frutos del mar, ceviche mixto, paella; no mollusk-only words), CRC and USD, the America/Costa_Rica time zone and the Wikivoyage ZIM reference. The pack is validated against a schema at startup and a broken pack stops the app with a clear error. A request with a line of menu text returns an answer card naming the matched Allergen Terms as evidence; matching ignores accents and case. Peanut is a fake Allergen that exists only in a YAML test-fixture pack.

## Acceptance criteria

- [ ] The `cr` pack loads from YAML and passes schema validation; an invalid pack fails at startup with a message naming the problem
- [ ] Adding or removing a term in the YAML changes what matches, proven by a test
- [ ] Term matching ignores accents and case ("CAMARON" matches camarón)
- [ ] Mollusk-only words (calamar, pulpo, almeja…) do not match shellfish
- [ ] Peanut terms appear only in the test-fixture pack
- [ ] False positives of accent-insensitive matching are measured and written to `docs/results/`

## Blocked by

- None (can start immediately)

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with the scripted OpenAI-compatible server. Use real OCR, DuckDB and the specimen Country Pack. Pass time and GPS in through requests.
