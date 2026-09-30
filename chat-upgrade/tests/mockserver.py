"""A tiny OpenAI-compatible server for tests: streaming, logprobs, slow and silent modes."""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, List, Optional


class MockLLM:
    def __init__(self) -> None:
        self.requests: List[Dict] = []
        self.reply_pieces: List[str] = ["안녕", "하세요.", " 반가워요."]
        self.piece_delay = 0.0
        self.first_delay = 0.0
        self.logprobs: Optional[Callable[[Dict], List[tuple]]] = None   # body -> [(token, logprob)]
        self.status = 200
        self._server = None
        self._thread = None

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> "MockLLM":
        mock = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def do_POST(self):
                n = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                mock.requests.append(body)
                if mock.status != 200:
                    data = b'{"error":{"message":"boom"}}'
                    self.send_response(mock.status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if body.get("stream"):
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    try:
                        time.sleep(mock.first_delay)
                        for piece in mock.reply_pieces:
                            chunk = {"choices": [{"index": 0, "delta": {"content": piece}}]}
                            self.wfile.write(("data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n").encode())
                            self.wfile.flush()
                            time.sleep(mock.piece_delay)
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    except OSError:          # client went away (cancel, stall test)
                        pass
                    self.close_connection = True
                    return
                choice = {"index": 0, "message": {"role": "assistant", "content": "".join(mock.reply_pieces)}}
                if body.get("logprobs") and mock.logprobs is not None:
                    top = mock.logprobs(body)
                    choice["message"]["content"] = top[0][0] if top else ""
                    choice["logprobs"] = {"content": [{
                        "token": top[0][0] if top else "", "logprob": top[0][1] if top else 0.0,
                        "top_logprobs": [{"token": t, "logprob": lp, "bytes": list(t.encode())} for t, lp in top],
                    }]}
                data = json.dumps({"choices": [choice]}, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()


class MockJulia:
    """Stands in for tools/julia_router.py --serve: POST /predict, GET /health.
    `scores(body) -> [score per option]` is turned into probabilities."""

    def __init__(self, scores: Optional[Callable[[Dict], List[float]]] = None) -> None:
        self.requests: List[Dict] = []
        self.scores = scores or (lambda body: [1.0] * len(body["options"]))
        self.status = 200
        self.raw: Optional[Dict] = None          # send this reply instead
        self._server = None
        self._thread = None

    @property
    def url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def start(self) -> "MockJulia":
        mock = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def _send(self, code, obj):
                data = json.dumps(obj, ensure_ascii=False).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                self._send(200, {"ok": True, "model": "mock-julia"})

            def do_POST(self):
                n = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                mock.requests.append(body)
                if mock.status != 200:
                    self._send(mock.status, {"error": "boom"})
                    return
                if mock.raw is not None:
                    self._send(200, mock.raw)
                    return
                s = [float(x) for x in mock.scores(body)]
                t = sum(s)
                self._send(200, {"probabilities": [x / t for x in s]})

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
