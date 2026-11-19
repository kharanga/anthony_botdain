import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from travel_companion.chat_message import ChatMessage
from travel_companion.prompt_budget import REPLY_TOKENS, fit_to_prompt_budget

REQUEST_TIMEOUT_SECONDS = 120.0


class ModelUnavailable(Exception):
    pass


@dataclass(frozen=True)
class ModelClient:
    endpoint_url: str

    def complete(self, messages: list[ChatMessage]) -> str:
        fitted_messages = fit_to_prompt_budget(messages)
        request_body = {
            "messages": [{"role": message.role, "content": message.content} for message in fitted_messages],
            "max_tokens": REPLY_TOKENS,
            "stream": False,
        }
        response_body = self.post_json(request_body)
        try:
            return response_body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ModelUnavailable(f"unexpected reply shape: {error}") from error

    def post_json(self, request_body: dict) -> dict:
        http_request = urllib.request.Request(
            self.endpoint_url,
            data=json.dumps(request_body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=REQUEST_TIMEOUT_SECONDS) as http_response:
                return json.loads(http_response.read())
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as error:
            raise ModelUnavailable(str(error)) from error
