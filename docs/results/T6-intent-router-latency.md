# T6: Intent router latency

Run on 2026-11-19 with `.venv/bin/python -m travel_companion.intent_router_benchmark`.

## Machine

- arm64, Darwin 27.2.0
- Python 3.13.2

## Method

Each of the 50 sample transcripts in `specimens/intent_samples.toml` is routed 200 times in-process through `route_transcript` (the same call `POST /api/transcript` makes), after one warm-up call. The time per sample is the median of those runs. It covers the rules and building the answer card; HTTP and speech-to-text are not included. No model call is made on any sample.

## Summary

- Routed correctly: 50 of 50
- Median routing time: 20.1 µs
- 95th percentile: 54.9 µs
- Slowest sample: 62.1 µs

## Per sample

| Transcript | Expected intent | Routed correctly | Median, µs |
| --- | --- | --- | --- |
| show my allergy card | show_staff_phrase | yes | 4.9 |
| Show the allergy card please. | show_staff_phrase | yes | 5.2 |
| open the staff phrase | show_staff_phrase | yes | 5.2 |
| How do I say I'm allergic to shellfish? | show_staff_phrase | yes | 7.2 |
| I need to tell the waiter about my allergy | show_staff_phrase | yes | 7.9 |
| help me ask the waiter what's in this dish | show_staff_phrase | yes | 7.7 |
| show the hospital phrase | show_staff_phrase | yes | 5.5 |
| does the third one have shrimp? | menu_allergen_question | yes | 20.1 |
| Does number 4 have lobster | menu_allergen_question | yes | 18.6 |
| is there crab in the second dish | menu_allergen_question | yes | 19.5 |
| does dish seven contain shellfish | menu_allergen_question | yes | 20.7 |
| any shrimp in the first one? | menu_allergen_question | yes | 19.5 |
| does the ceviche have shrimp | menu_allergen_question | yes | 18.6 |
| is there crab in the arroz con mariscos | menu_allergen_question | yes | 23.8 |
| is the last one ok for my allergy | menu_allergen_question | yes | 21.6 |
| which dishes on this menu have prawns | menu_allergen_question | yes | 22.4 |
| Where can I see sloths near La Fortuna? | guide_question | yes | 23.4 |
| what is the best beach in Manuel Antonio | guide_question | yes | 23.6 |
| how do I get from San José to Monteverde | guide_question | yes | 24.8 |
| When is the rainy season in Costa Rica? | guide_question | yes | 23.0 |
| is the tap water drinkable in Tamarindo | guide_question | yes | 22.5 |
| tell me about Arenal volcano | guide_question | yes | 18.3 |
| where can I eat lobster in Puerto Viejo | guide_question | yes | 24.2 |
| do I need a visa for Costa Rica | guide_question | yes | 21.1 |
| how much does a taxi from the airport cost? | guide_question | yes | 24.9 |
| I spent five mil on a taxi | add_expense | yes | 31.6 |
| I paid 12 dollars for lunch | add_expense | yes | 18.4 |
| add an expense of ₡3.500 for coffee | add_expense | yes | 27.0 |
| spent 5 rojos at the soda | add_expense | yes | 20.8 |
| I paid $45 for the zipline tour | add_expense | yes | 49.8 |
| add 80 dollars for the hotel | add_expense | yes | 42.1 |
| I spent twenty five hundred colones on a bus ticket | add_expense | yes | 43.0 |
| I just spent 15,000 colones on souvenirs | add_expense | yes | 62.1 |
| I paid 7.50 for parking | add_expense | yes | 34.6 |
| How much have I spent on food? | spending_question | yes | 20.1 |
| how much did I spend today | spending_question | yes | 54.9 |
| what's my total spending | spending_question | yes | 54.9 |
| how much have I spent on taxis this week | spending_question | yes | 32.3 |
| what did I spend on lodging yesterday | spending_question | yes | 45.8 |
| show my boarding pass | open_vault | yes | 5.8 |
| open my passport | open_vault | yes | 5.8 |
| open the vault | open_vault | yes | 8.1 |
| pull up my travel insurance | open_vault | yes | 7.4 |
| show me my hotel reservation | open_vault | yes | 9.1 |
| where's my driver's license | open_vault | yes | 8.5 |
| play some music | unsupported (I can't do that yet) | yes | 12.9 |
| set a timer for ten minutes | unsupported (I can't do that yet) | yes | 19.2 |
| call my mom | unsupported (I can't do that yet) | yes | 12.0 |
| turn on the flashlight | unsupported (I can't do that yet) | yes | 15.1 |
| take a selfie | unsupported (I can't do that yet) | yes | 12.4 |
