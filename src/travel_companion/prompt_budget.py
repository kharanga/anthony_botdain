import math

from travel_companion.chat_message import ChatMessage

MODEL_CONTEXT_TOKENS = 2048
REPLY_TOKENS = 256
CHAT_TEMPLATE_TOKENS_PER_MESSAGE = 8
SAFETY_MARGIN_TOKENS = 64
PROMPT_TOKEN_BUDGET = MODEL_CONTEXT_TOKENS - REPLY_TOKENS - SAFETY_MARGIN_TOKENS
BYTES_PER_TOKEN_FOR_NON_DIGITS = 2


class PromptTooLong(Exception):
    pass


def estimated_tokens(text: str) -> int:
    digit_count = sum(character.isdigit() for character in text)
    non_digit_bytes = len(text.encode()) - digit_count
    return digit_count + math.ceil(non_digit_bytes / BYTES_PER_TOKEN_FOR_NON_DIGITS)


def estimated_prompt_tokens(messages: list[ChatMessage]) -> int:
    return sum(
        estimated_tokens(message.content) + CHAT_TEMPLATE_TOKENS_PER_MESSAGE for message in messages
    )


def longest_prefix_within(text: str, token_budget: int) -> str:
    shortest_too_long, longest_fitting = len(text) + 1, 0
    while shortest_too_long - longest_fitting > 1:
        candidate_length = (shortest_too_long + longest_fitting) // 2
        if estimated_tokens(text[:candidate_length]) <= token_budget:
            longest_fitting = candidate_length
        else:
            shortest_too_long = candidate_length
    return text[:longest_fitting]


def fit_to_prompt_budget(messages: list[ChatMessage]) -> list[ChatMessage]:
    if estimated_prompt_tokens(messages) <= PROMPT_TOKEN_BUDGET:
        return messages
    *leading_messages, last_message = messages
    tokens_left_for_last = (
        PROMPT_TOKEN_BUDGET - estimated_prompt_tokens(leading_messages) - CHAT_TEMPLATE_TOKENS_PER_MESSAGE
    )
    if tokens_left_for_last <= 0:
        raise PromptTooLong(f"leading messages alone exceed {PROMPT_TOKEN_BUDGET} tokens")
    trimmed_content = longest_prefix_within(last_message.content, tokens_left_for_last)
    return [*leading_messages, ChatMessage(last_message.role, trimmed_content)]
