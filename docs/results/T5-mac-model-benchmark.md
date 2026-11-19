# T5: Mac model benchmark

Run on 2026-11-18 with `.venv/bin/python -m travel_companion.model_benchmark`.

## Machine

- Chip: Apple M2
- Memory: 8 GB
- OS: macOS 27.2
- llama-server: 1.0.0 (build 12359, commit b1b770d90)
- Model: `qwen2.5-1.5b-instruct-q4_k_m.gguf`, 2,048-token context, all layers on the GPU (`scripts/start_model_server.sh`)

## Summary

- Model load time: 1.4 s (from starting llama-server until `/health` answers)
- Peak resident memory of llama-server: 1198.0 MB
- macOS memory footprint of llama-server at the end of the run: 186.0 MB
- Guardrail rejection rate: 16 of 108 replies (15%)

Resident memory is sampled from `ps` every 0.1 s for the whole run and includes the memory-mapped model weights. The footprint (from `footprint`) counts only memory macOS cannot reclaim by dropping clean file-backed pages, so it leaves the weights out.

## Speed

Each prompt was streamed 5 times with the prompt cache off, after one warm-up request. Values are the median, with the range in brackets. Time to first token is measured by the client from sending the request to the first streamed content chunk. Tokens per second counts streamed chunks after the first, divided by the time between the first and last chunk. Prompt tokens are the app's own estimate (`prompt_budget.py`).

| Prompt | Prompt tokens (estimate) | Time to first token, s | Tokens per second | Reply tokens |
| --- | --- | --- | --- | --- |
| short question (/api/ask) | 72 | 0.090 (0.084–0.112) | 66.5 (63.7–68.6) | 39 |
| phrase the Rate from facts (/api/ask/rate) | 163 | 0.127 (0.124–0.128) | 65.1 (62.8–70.1) | 11 |
| long question trimmed to the prompt budget | 1728 | 1.005 (1.002–1.012) | 65.9 (64.6–67.1) | 78 |

## Guardrail on real-model output

108 replies: 12 fixed Rate questions at 3 Rates, each asked 3 times, through the same prompt and checks as `POST /api/ask/rate`, with llama-server's default sampling. A rejected reply is replaced by the template answer on the card, so the user still sees the correct Rate.

| Verdict | Replies |
| --- | --- |
| kept | 92 |
| rejected: added a name | 2 |
| rejected: dropped or changed a fact | 14 |

| Rate | Rejected |
| --- | --- |
| 510 | 5 of 36 (14%) |
| 505.5 | 5 of 36 (14%) |
| 498 | 6 of 36 (17%) |

### Every reply

| Rate | Question | Model reply | Verdict |
| --- | --- | --- | --- |
| 510 | What is the rate? | The rate is 510 CRC per USD. | kept |
| 510 | How many colones do I get for one dollar? | For every USD 1, you get 510 CRC. | kept |
| 510 | What's the exchange rate today? | Today's exchange rate is 510 CRC per USD. | kept |
| 510 | If I change one US dollar, how many colones is that? | With one US dollar, you would receive 510 colons. | kept |
| 510 | What is a dollar worth in Costa Rica? | 1 CRC per USD | rejected: dropped or changed a fact |
| 510 | Tell me the colón to dollar rate. | The colón to dollar rate is 510 CRC per USD. | kept |
| 510 | How much is 1 USD in CRC? | 1 USD is equivalent to 510 CRC. | kept |
| 510 | Is the dollar strong against the colón right now? | No, the dollar is not strong against the colón right now. | rejected: dropped or changed a fact |
| 510 | What rate should I expect when paying in dollars? | When paying in dollars, you should expect a rate of 510 CRC per USD. | kept |
| 510 | Convert one dollar to colones for me. | One dollar is equivalent to 510 colones. | kept |
| 510 | What's the rate for US dollars? | The rate is 510 CRC per USD. | kept |
| 510 | How many ₡ per $? | The rate is 510 CRC per USD. | kept |
| 505.5 | What is the rate? | The rate is 505.5 CRC per USD. | kept |
| 505.5 | How many colones do I get for one dollar? | For every US dollar, you get 505.5 colons. | kept |
| 505.5 | What's the exchange rate today? | The exchange rate is 505.5 CRC per USD. | kept |
| 505.5 | If I change one US dollar, how many colones is that? | If you change one US dollar, it is equivalent to 505.5 colones. | kept |
| 505.5 | What is a dollar worth in Costa Rica? | 505.5 Costa Rican Colones (CRC) per US dollar. | rejected: added a name |
| 505.5 | Tell me the colón to dollar rate. | 505.5 CRC per USD | kept |
| 505.5 | How much is 1 USD in CRC? | 1 USD is equivalent to 505.5 CRC. | kept |
| 505.5 | Is the dollar strong against the colón right now? | The statement doesn't provide information about the current strength of the dollar against the colón. | rejected: dropped or changed a fact |
| 505.5 | What rate should I expect when paying in dollars? | When paying in dollars, you should expect a rate of 505.5 CRC per USD. | kept |
| 505.5 | Convert one dollar to colones for me. | 1 USD = 505.5 CRC | kept |
| 505.5 | What's the rate for US dollars? | The rate for US dollars is 505.5 CRC per USD. | kept |
| 505.5 | How many ₡ per $? | 505.5 CRC per USD. | kept |
| 498 | What is the rate? | The rate is 498 CRC per USD. | kept |
| 498 | How many colones do I get for one dollar? | For every 1 USD, you get 498 CRC colones. | kept |
| 498 | What's the exchange rate today? | The exchange rate is 498 CRC per USD. | kept |
| 498 | If I change one US dollar, how many colones is that? | If you change one US dollar, that is equivalent to 498 colones. | kept |
| 498 | What is a dollar worth in Costa Rica? | 1 USD = 498 CRC | kept |
| 498 | Tell me the colón to dollar rate. | The rate is 498 CRC per USD. | kept |
| 498 | How much is 1 USD in CRC? | 1 USD is equivalent to 498 CRC. | kept |
| 498 | Is the dollar strong against the colón right now? | Based on the rate of 498 CRC per USD, the dollar is not strong against the colón right now. | kept |
| 498 | What rate should I expect when paying in dollars? | You should expect a rate of 498 CRC per USD when paying in dollars. | kept |
| 498 | Convert one dollar to colones for me. | 498 colons (CRC) per dollar. | kept |
| 498 | What's the rate for US dollars? | The rate is 498 CRC per USD. | kept |
| 498 | How many ₡ per $? | To convert the rate from US dollars to Cuban pesos, you would divide the rate by 498. | rejected: dropped or changed a fact |
| 510 | What is the rate? | The rate is 510 CRC per USD. | kept |
| 510 | How many colones do I get for one dollar? | For every USD, you get 510 colones. | kept |
| 510 | What's the exchange rate today? | The exchange rate is 510 CRC per USD. | kept |
| 510 | If I change one US dollar, how many colones is that? | With one US dollar, you would get 510 colons. | kept |
| 510 | What is a dollar worth in Costa Rica? | A dollar is worth 510 Costa Rican Colones (CRC) according to the rate provided. | rejected: added a name |
| 510 | Tell me the colón to dollar rate. | The rate is 510 CRC per USD. | kept |
| 510 | How much is 1 USD in CRC? | 1 USD is equivalent to 510 CRC. | kept |
| 510 | Is the dollar strong against the colón right now? | No, the dollar is not strong against the colón right now. | rejected: dropped or changed a fact |
| 510 | What rate should I expect when paying in dollars? | You should expect a rate of 510 CRC per USD when paying in dollars. | kept |
| 510 | Convert one dollar to colones for me. | 1 USD = 510 CRC | kept |
| 510 | What's the rate for US dollars? | The rate for US dollars is 510 CRC per USD. | kept |
| 510 | How many ₡ per $? | To convert the rate from USD to ₡, you would multiply by 510. | kept |
| 505.5 | What is the rate? | The rate is 505.5 CRC per USD. | kept |
| 505.5 | How many colones do I get for one dollar? | For 1 USD, you get 505.5 CRC. | kept |
| 505.5 | What's the exchange rate today? | The exchange rate is 505.5 CRC per USD. | kept |
| 505.5 | If I change one US dollar, how many colones is that? | If you change one US dollar, it is equivalent to 505.5 colones. | kept |
| 505.5 | What is a dollar worth in Costa Rica? | 1 USD = 505.5 CRC | kept |
| 505.5 | Tell me the colón to dollar rate. | The rate is 505.5 CRC per USD. | kept |
| 505.5 | How much is 1 USD in CRC? | 1 USD is equivalent to 505.5 CRC. | kept |
| 505.5 | Is the dollar strong against the colón right now? | The rate of 505.5 CRC per USD indicates that the colón is weak against the dollar. | kept |
| 505.5 | What rate should I expect when paying in dollars? | When paying in dollars, you should expect a rate of 505.5 CRC per USD. | kept |
| 505.5 | Convert one dollar to colones for me. | To convert one dollar to colones, multiply the rate by 1: 505.5 CRC. | kept |
| 505.5 | What's the rate for US dollars? | The rate for US dollars is 505.5 CRC per USD. | kept |
| 505.5 | How many ₡ per $? | 505.5 CRC per USD. | kept |
| 498 | What is the rate? | The rate is 498 CRC per USD. | kept |
| 498 | How many colones do I get for one dollar? | 498 colones. | rejected: dropped or changed a fact |
| 498 | What's the exchange rate today? | The exchange rate is 498 CRC per USD. | kept |
| 498 | If I change one US dollar, how many colones is that? | With one US dollar, you get 498 colones. | kept |
| 498 | What is a dollar worth in Costa Rica? | 1 CRC per USD. | rejected: dropped or changed a fact |
| 498 | Tell me the colón to dollar rate. | The rate is 498 CRC per USD. | kept |
| 498 | How much is 1 USD in CRC? | 1 USD is equivalent to 498 CRC. | kept |
| 498 | Is the dollar strong against the colón right now? | No, the dollar is not strong against the colón right now based on the given rate of 498 CRC per USD. | kept |
| 498 | What rate should I expect when paying in dollars? | When paying in dollars, you should expect a rate of 498 CRC per USD. | kept |
| 498 | Convert one dollar to colones for me. | 498 CRC. | rejected: dropped or changed a fact |
| 498 | What's the rate for US dollars? | The rate for US dollars is 498 CRC per USD. | kept |
| 498 | How many ₡ per $? | To convert ₡ to $, divide by 498. | kept |
| 510 | What is the rate? | The rate is 510 CRC per USD. | kept |
| 510 | How many colones do I get for one dollar? | For every USD 1, you get 510 CRC. | kept |
| 510 | What's the exchange rate today? | Today's exchange rate is 510 CRC per USD. | kept |
| 510 | If I change one US dollar, how many colones is that? | If you change one US dollar, it is equivalent to 510 colones. | kept |
| 510 | What is a dollar worth in Costa Rica? | 1 USD = 0.0195 CRC | rejected: dropped or changed a fact |
| 510 | Tell me the colón to dollar rate. | The colón to dollar rate is 510 CRC per USD. | kept |
| 510 | How much is 1 USD in CRC? | 1 USD is equivalent to 510 CRC. | kept |
| 510 | Is the dollar strong against the colón right now? | No, the dollar is not strong against the colón right now, as it's stated that the rate is 510 CRC per USD. | kept |
| 510 | What rate should I expect when paying in dollars? | When paying in dollars, you should expect a rate of 510 CRC per USD. | kept |
| 510 | Convert one dollar to colones for me. | To convert one dollar to colones, multiply by 510. | kept |
| 510 | What's the rate for US dollars? | The rate for US dollars is 510 CRC per USD. | kept |
| 510 | How many ₡ per $? | 510 CRC per USD. | kept |
| 505.5 | What is the rate? | The rate is 505.5 CRC per USD. | kept |
| 505.5 | How many colones do I get for one dollar? | For one dollar, you get 505.5 colones. | kept |
| 505.5 | What's the exchange rate today? | The exchange rate is 505.5 CRC per USD today. | kept |
| 505.5 | If I change one US dollar, how many colones is that? | 505.5 colones. | rejected: dropped or changed a fact |
| 505.5 | What is a dollar worth in Costa Rica? | 1 USD = 0.02 CRC | rejected: dropped or changed a fact |
| 505.5 | Tell me the colón to dollar rate. | The rate is 505.5 CRC per USD. | kept |
| 505.5 | How much is 1 USD in CRC? | 1 USD is equivalent to 505.5 CRC. | kept |
| 505.5 | Is the dollar strong against the colón right now? | The given rate of 505.5 CRC per USD indicates that the dollar is weak against the colón. | kept |
| 505.5 | What rate should I expect when paying in dollars? | When paying in dollars, you should expect a rate of 505.5 CRC per USD. | kept |
| 505.5 | Convert one dollar to colones for me. | 505.5 colones. | rejected: dropped or changed a fact |
| 505.5 | What's the rate for US dollars? | The rate for US dollars is 505.5 CRC per USD. | kept |
| 505.5 | How many ₡ per $? | 505.5 CRC per USD is the rate. | kept |
| 498 | What is the rate? | The rate is 498 CRC per USD. | kept |
| 498 | How many colones do I get for one dollar? | 498 colones. | rejected: dropped or changed a fact |
| 498 | What's the exchange rate today? | The current exchange rate is 498 CRC per USD. | kept |
| 498 | If I change one US dollar, how many colones is that? | 1 US dollar is equivalent to 498 colons. | kept |
| 498 | What is a dollar worth in Costa Rica? | 1 USD = 498 CRC | kept |
| 498 | Tell me the colón to dollar rate. | The rate is 498 CRC per USD. | kept |
| 498 | How much is 1 USD in CRC? | 1 USD is equivalent to 498 CRC. | kept |
| 498 | Is the dollar strong against the colón right now? | Based on the information provided, the dollar is not strong against the colón right now. | rejected: dropped or changed a fact |
| 498 | What rate should I expect when paying in dollars? | You should expect 498 CRC per dollar. | kept |
| 498 | Convert one dollar to colones for me. | 498 colones (CRC) per USD. | kept |
| 498 | What's the rate for US dollars? | 498 CRC per USD | kept |
| 498 | How many ₡ per $? | 498 CRC per USD. | kept |

## Notes on this run (written by hand; a rerun replaces this file)

- Speed is not a concern on the Mac: the Rate answer starts in about 0.13 s, and even a prompt filled to the budget starts in about 1 s.
- Peak resident memory stays near 1.2 GB on an 8 GB Mac, close to the "about 1 GB" in the README.
- Most rejections are correct: wrong conversions ("1 USD = 0.02 CRC"), invented currencies ("Cuban pesos"), and replies to "Is the dollar strong?" that drop the Rate.
- Some rejections are stricter than they need to be: short replies such as "498 colones." keep the Rate but drop the dollar term, and "Costa Rican Colones" is rejected as an added name. In both cases the card still shows the correct template answer.
- The rejection rate moves between runs because llama-server samples at its default temperature. Earlier runs on the same day gave 7 of 36 (19%), three times, and 3 of 36 (8%), once.
