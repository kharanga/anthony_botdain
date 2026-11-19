# travel-companion

An offline device that answers a traveller's questions about food allergens, money, plans and places in one country, using only data carried on the device.

## Scope

**Trip Build**:
The features that must work on the Pi by the trip: menu allergen scanner, staff phrase card, push-to-talk questions, offline guide, expenses and document vault.
_Avoid_: MVP, v1

**Backlog**:
Features planned but outside the Trip Build: itinerary and "What's next?", transit helper, landmark guide.
_Avoid_: dropped, cut

**Capture Mode**:
Saving a photo with its GPS position and time on the trip, to build real test sets for Backlog features.
_Avoid_: logging, recording

## Photos

**Photo Kind**:
What a photo shows, as confirmed by the user: menu, receipt, ticket, sign, document or other. The Photo Kind decides which feature handles the photo.
_Avoid_: photo type, category, class

**Suggested Kind**:
The router's guess at a photo's Photo Kind, shown for the user to confirm or change.
_Avoid_: prediction, auto-kind

## Country

**Country Pack**:
The bundle of facts for one country: allergen terms, known dishes, phrases, currency, time zone and guide.
_Avoid_: locale, region pack

## Allergy

**Allergen**:
A food the traveller must avoid; several can be active at once. The trip Allergen is shellfish, meaning crustaceans (shrimp, lobster, crab); mollusks are not shellfish here. Peanut is a fake Allergen used only in specimen data.
_Avoid_: allergy, trigger

**Allergen Term**:
A word in the country's language that means a dish probably contains an Allergen, such as "camarones" or the mixed-seafood word "mariscos".
_Avoid_: keyword

**Known Dish**:
A dish in the Country Pack, with its aliases and its Ingredients, each entry taken from a recorded source.
_Avoid_: recipe, menu item

**Ingredient**:
One component of a Known Dish, marked **usual** (almost always in the dish) or **sometimes** (depends on the kitchen).
_Avoid_: component

**Menu Line**:
One line of text read from a menu photo, the unit that gets Allergy Labels.
_Avoid_: menu item, entry

**Allergy Label**:
The verdict on a Menu Line for one Allergen, exactly one of:
- **Contains**: the line has an Allergen Term, or its matched Known Dish has the Allergen as a usual Ingredient.
- **Often contains**: its matched Known Dish has the Allergen as a sometimes Ingredient.
- **Not typical**: it matched a Known Dish, and the Allergen is not among its Ingredients.
- **Ask staff**: no Known Dish matched, or the line is unreadable.

_Avoid_: safe, risk score, rating

**Warning**:
What the traveller sees for a Contains or Often contains label: the Allergen and the Ingredient or Allergen Term behind it.
_Avoid_: alert, flag

## Phrases

**Phrase**:
A sentence in the country's language for the traveller to show staff, such as the allergy explanation.
_Avoid_: translation, sentence

**Machine-checked**:
The verification status of a Phrase checked only by a translation tool or an LLM, not by a native speaker. Every Phrase in the Trip Build is Machine-checked.
_Avoid_: verified, translated

## Money

**Expense**:
A record of money spent during the trip, holding one amount in the currency actually paid (colones or US dollars). The other currency is shown by converting at the Rate when viewed.
_Avoid_: transaction, purchase, receipt

**Rate**:
The exchange rate between the two currencies, entered by hand in config because the device is offline.
_Avoid_: live rate, FX
