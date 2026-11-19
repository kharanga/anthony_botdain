# #20: App boots and returns an answer card

**Parent:** #2  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/20

## Parent

#2

## What to build

The app starts on the Mac and the config loads: country=cr, active Allergens=[shellfish], home currency=USD, Rate (colones per dollar), model endpoint URL. A status request returns an answer card with an evidence field, and the web UI shell shows it in a browser tab. This sets up the HTTP-API test harness and the gitignored data folder.

## Acceptance criteria

- [ ] The app starts on the Mac and the UI shell loads in a browser tab
- [ ] Config loads with the values above
- [ ] A status request through the HTTP API returns an answer card with evidence
- [ ] A test harness drives the app through its HTTP API
- [ ] The data folder exists and is gitignored
- [ ] A fresh clone runs with fake data alone

## Blocked by

- None (can start immediately)
