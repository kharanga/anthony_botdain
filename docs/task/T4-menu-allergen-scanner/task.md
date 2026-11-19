# #6: T4: Menu allergen scanner

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/6

Part of #1.

## What to build

Given OCR'd Menu Lines and the active Allergens, return one Allergy Label per line per Allergen, the Warnings, and the summary.

Label rules: Contains = the line has an Allergen Term, or the matched Known Dish has the Allergen as a usual Ingredient. Often contains = the matched dish has it as a sometimes Ingredient. Not typical = a dish matched and the Allergen is in neither list. Ask staff = no match, or the line is unreadable or low-confidence.

Matching uses aliases, ignores accents and case, and tolerates OCR typos. A weak match counts as no match. Ingredient words on the line are added to the dish's Ingredients.

Display: Warnings only for Contains and Often contains, at the top, one per Allergen, strongest first, each naming the Allergen and the Ingredient or Allergen Term. Ask staff lines get a grey "unknown dish — ask staff" note. Not typical lines get no marker. The summary always gives both counts ("No warnings in 12 known dishes. 4 unknown dishes — ask staff."). The allergy card is one tap away. The word "safe", a green check or "all clear" never appears.

## Blocked by

#3 (T2), #4 (T3), #5 (T5)

## Done when

- ≥95% recall on crustacean dishes in the specimen set
- Every label rule and display rule covered by tests
- A test checks that "safe" never appears in allergy output

## User stories

12–32 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
