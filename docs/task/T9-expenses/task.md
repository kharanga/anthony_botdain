# #9: T9: Expenses

**Parent:** #1  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/9

Part of #1.

## What to build

A receipt photo or a spoken sentence pre-fills an Expense (amount, currency, place, date, category) for the user to confirm or edit. Currency defaults to the one on the receipt, with a one-tap toggle. Parses ₡5.000, 5 mil, 5 rojos and USD. Each Expense stores one amount and the currency paid; conversion uses the config Rate at view time. Categories: food, transport, lodging, activities, shopping, other, with a suggestion from the text. Spending questions run as read-only natural-language-to-SQL with the SQL shown.

## Blocked by

#4 (T3), #5 (T5)

## Done when

- All ₡ formats parsed in tests
- Changing the Rate changes the totals shown
- A spending question can't change data

## User stories

55–65 in #1.

## Testing

Test through the app's HTTP API and check only the answer cards that come back. Fake the model endpoint with a scripted OpenAI-compatible server. Use real OCR, DuckDB, the specimen Country Pack and the Kiwix ZIM. Pass the current time and GPS position in through requests.
