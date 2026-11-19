import json
import threading
from collections import deque
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CHAT_COMPLETIONS_PATH = "/v1/chat/completions"
UNSCRIPTED_REPLY_STATUS = 500


@dataclass(frozen=True)
class ScriptedReply:
    status: int
    content: str


class FakeModelServer:
    def __init__(self) -> None:
        self.received_requests: list[dict] = []
        self.scripted_replies: deque[ScriptedReply] = deque()
        self.lock = threading.Lock()
        self.http_server = ThreadingHTTPServer(("127.0.0.1", 0), self.handler_class())
        self.thread = threading.Thread(
            target=self.http_server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        )

    @property
    def endpoint_url(self) -> str:
        host, port = self.http_server.server_address[:2]
        return f"http://{host}:{port}{CHAT_COMPLETIONS_PATH}"

    @property
    def last_request(self) -> dict:
        return self.received_requests[-1]

    def reply_with(self, *contents: str) -> None:
        with self.lock:
            self.scripted_replies.extend(ScriptedReply(200, content) for content in contents)

    def fail_with(self, status: int) -> None:
        with self.lock:
            self.scripted_replies.append(ScriptedReply(status, ""))

    def start(self) -> "FakeModelServer":
        self.thread.start()
        return self

    def stop(self) -> None:
        self.http_server.shutdown()
        self.http_server.server_close()
        self.thread.join()

    def record_and_pick_reply(self, request_body: dict) -> ScriptedReply:
        with self.lock:
            self.received_requests.append(request_body)
            if self.scripted_replies:
                return self.scripted_replies.popleft()
            return ScriptedReply(UNSCRIPTED_REPLY_STATUS, "")

    def handler_class(self) -> type[BaseHTTPRequestHandler]:
        fake_server = self

        class ChatCompletionsHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                if self.path != CHAT_COMPLETIONS_PATH:
                    self.send_json(404, {"error": {"message": f"unknown path {self.path}"}})
                    return
                body_length = int(self.headers.get("Content-Length", "0"))
                request_body = json.loads(self.rfile.read(body_length))
                reply = fake_server.record_and_pick_reply(request_body)
                if reply.status != 200:
                    self.send_json(reply.status, {"error": {"message": "scripted failure"}})
                    return
                self.send_json(200, chat_completion_body(reply.content))

            def send_json(self, status: int, body: dict) -> None:
                encoded = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, format: str, *args) -> None:
                pass

        return ChatCompletionsHandler


def chat_completion_body(content: str) -> dict:
    return {
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "model": "fake-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }
