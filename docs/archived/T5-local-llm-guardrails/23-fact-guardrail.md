# #23: Fact guardrail

**Parent:** #5  
**Status:** closed  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/23

## Parent

#5

## What to build

When an answer is phrased from data facts (numbers, terms, names), a check rejects any LLM output that changes or adds a fact and falls back to a plain template answer.

## Acceptance criteria

- [ ] Fake replies that change a number, term or name are rejected
- [ ] Rejected answers fall back to a template answer built from the data
- [ ] The answer card's evidence still shows the source facts
- [ ] Fake replies that keep the facts pass through

## Blocked by

- #22
