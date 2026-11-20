# #22: Model endpoint with a fake server

**Parent:** #5  
**Status:** closed  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/22

## Parent

#5

## What to build

One model client talks to the OpenAI-compatible chat-completions endpoint set in config (ADR 0001). A test-only ask request returns an answer card whose text comes from the endpoint. A scripted fake OpenAI-compatible server is wired into the test harness for every later ticket.

## Acceptance criteria

- [ ] The ask request returns an answer card whose text comes from the model endpoint
- [ ] The endpoint URL comes from config only
- [ ] Tests run against a scripted fake server with no real model
- [ ] Prompts are kept within 2,048 tokens

## Blocked by

- #20
