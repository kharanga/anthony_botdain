# #21: Edit the Rate on the device

**Parent:** #2  
**Status:** closed  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/21

## Parent

#2

## What to build

The user changes the Rate in the UI. It's saved in DuckDB and survives a restart.

## Acceptance criteria

- [ ] DuckDB is set up in the data folder
- [ ] Changing the Rate through the UI updates it through the API
- [ ] The Rate survives an app restart
- [ ] Round-trip tested through the HTTP API

## Blocked by

- #20
