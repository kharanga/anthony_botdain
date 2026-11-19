# #24: Real llama.cpp on the Mac

**Parent:** #5  
**Status:** open  
**Labels:** ready-for-agent  
**GitHub:** https://github.com/kharanga/anthony_botdain/issues/24

## Parent

#5

## What to build

Download Qwen2.5-1.5B (GGUF, Q4_K_M), run the llama.cpp server, and point the same endpoint config at it. The ask demo works with the real model.

## Acceptance criteria

- [ ] The model downloads into a gitignored location
- [ ] The llama.cpp server runs locally with no network calls once the model is downloaded
- [ ] The ask request works against the real model by changing config only
- [ ] Setup steps documented in the README

## Blocked by

- #22
