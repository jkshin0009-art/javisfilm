"""Client for the chatbot's existing LLM server (llama.cpp llama-server or any
OpenAI-compatible server). Standard library only.

Three calls:
  stream_chat()          token stream for a spoken reply, cancellable, with a stall timeout
  chat()                 one full reply
  first_token_logprobs() the next-token distribution of the first reply token, used by
                         decide.py to read a typed decision without generating text
"""
from __future__ import annotations

import base64
import json
import os
import socket
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Sequence, Tuple


def image_part(path: str) -> Dict:
    """An OpenAI-style image content part (data URL) for a vision model behind
    llama-server (started with --mmproj)."""
    ext = os.path.splitext(path)[1].lower()
    mime = {".png": "image/png", ".webp": "image/webp"}.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def with_images(text: str, images: Sequence[str] = ()) -> object:
    """Message content: plain text, or the images first and the text last, so
    several questions about the same images share a cacheable prefix."""
    if not images:
        return text
    return [image_part(p) for p in images] + [{"type": "text", "text": text}]


class LLMError(RuntimeError):
    pass


class StallError(LLMError):
    """No bytes arrived from the server for `stall_timeout` seconds."""


class Cancelled(LLMError):
    """The caller cancelled the request (barge-in)."""


@dataclass
class FirstToken:
    text: str                                   # the token the server generated
    top: List[Tuple[str, float]] = field(default_factory=list)   # (token, logprob), best first; empty if unsupported

    @property
    def has_logprobs(self) -> bool:
        return bool(self.top)


def _shutdown(resp) -> None:
    """Unblock a thread sitting in resp.readline(). Closing the file object from
    another thread does not reliably wake a blocked recv; shutting the socket
    down does, and the reader then sees end of stream."""
    try:
        sock = resp.fp.raw._sock
        sock.shutdown(socket.SHUT_RDWR)
    except Exception:
        try:
            resp.close()
        except Exception:
            pass


class CancelToken:
    """Shared between the loop and a running request. cancel() closes the open
    HTTP response, which unblocks the reading thread; llama-server stops
    generating when the client disconnects."""

    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._resp = None

    def cancel(self) -> None:
        self._event.set()
        with self._lock:
            resp = self._resp
        if resp is not None:
            _shutdown(resp)

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def _attach(self, resp) -> None:
        with self._lock:
            self._resp = resp
        if self._event.is_set():
            self.cancel()

    def _detach(self) -> None:
        with self._lock:
            self._resp = None


class LLMClient:
    """base_url: e.g. http://127.0.0.1:5678 (the /v1 suffix is optional).

    thinking_off sends chat_template_kwargs={"enable_thinking": false}, which the
    Qwen3 family templates in llama-server honour, so the first generated token is
    the answer and not <think>. Leave it on for spoken replies too: a reply that
    spends its budget thinking is silence for the listener."""

    def __init__(self, base_url: str, model: Optional[str] = None, api_key: Optional[str] = None,
                 timeout: float = 120.0, thinking_off: bool = True,
                 extra: Optional[Dict] = None, slot_id: Optional[int] = None) -> None:
        base = base_url.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        self.base = base
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.thinking_off = thinking_off
        self.extra = dict(extra or {})
        self.slot_id = slot_id

    # ------------------------------------------------------------ plumbing
    def _payload(self, messages: Sequence[Dict], **kw) -> Dict:
        body: Dict = {"messages": list(messages)}
        if self.model:
            body["model"] = self.model
        if self.thinking_off:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        if self.slot_id is not None:
            body["id_slot"] = self.slot_id
        body["cache_prompt"] = True
        body.update(self.extra)
        body.update({k: v for k, v in kw.items() if v is not None})
        return body

    def _open(self, body: Dict, timeout: float):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base + "/v1/chat/completions", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", "Bearer " + self.api_key)
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise LLMError(f"HTTP {e.code} from {self.base}: {detail}") from None
        except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
            raise LLMError(f"cannot reach {self.base}: {e}") from None

    # ------------------------------------------------------------ calls
    def stream_chat(self, messages: Sequence[Dict], *, max_tokens: int = 400,
                    temperature: Optional[float] = 0.8, stop: Optional[List[str]] = None,
                    cancel: Optional[CancelToken] = None, stall_timeout: float = 60.0,
                    **params) -> Iterator[str]:
        """Yield content deltas. Raises StallError when the server goes quiet for
        stall_timeout seconds and Cancelled when `cancel` fires."""
        body = self._payload(messages, stream=True, max_tokens=max_tokens,
                             temperature=temperature, stop=stop, **params)
        resp = self._open(body, timeout=stall_timeout)
        if cancel is not None:
            cancel._attach(resp)
        try:
            while True:
                if cancel is not None and cancel.cancelled:
                    raise Cancelled("cancelled")
                try:
                    raw = resp.readline()
                except socket.timeout:
                    raise StallError(f"no data for {stall_timeout:.0f}s") from None
                except (ValueError, OSError, AttributeError):
                    # closed underneath us by cancel(); anything else is a real error
                    if cancel is not None and cancel.cancelled:
                        raise Cancelled("cancelled") from None
                    raise
                if not raw:
                    if cancel is not None and cancel.cancelled:
                        raise Cancelled("cancelled")
                    return
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    return
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if "error" in obj:
                    raise LLMError(str(obj["error"])[:500])
                for ch in obj.get("choices") or []:
                    delta = ch.get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        yield piece
        finally:
            if cancel is not None:
                cancel._detach()
            try:
                resp.close()
            except Exception:
                pass

    def chat(self, messages: Sequence[Dict], *, max_tokens: int = 400,
             temperature: Optional[float] = 0.8, stop: Optional[List[str]] = None, **params) -> str:
        body = self._payload(messages, stream=False, max_tokens=max_tokens,
                             temperature=temperature, stop=stop, **params)
        with self._open(body, timeout=self.timeout) as resp:
            obj = json.loads(resp.read().decode("utf-8", "replace"))
        try:
            return obj["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"unexpected response: {str(obj)[:300]}") from None

    def first_token_logprobs(self, messages: Sequence[Dict], top_n: int = 20) -> FirstToken:
        """Generate one token greedily and return the server's top_n next-token
        log-probabilities for it. llama-server reports them from a plain softmax of
        the logits, before any sampler, which is what a decision readout needs.
        A server that ignores `logprobs` gives FirstToken(text, top=[])."""
        body = self._payload(messages, stream=False, max_tokens=1, temperature=0.0,
                             logprobs=True, top_logprobs=int(top_n))
        with self._open(body, timeout=self.timeout) as resp:
            obj = json.loads(resp.read().decode("utf-8", "replace"))
        try:
            choice = obj["choices"][0]
        except (KeyError, IndexError, TypeError):
            raise LLMError(f"unexpected response: {str(obj)[:300]}") from None
        text = ((choice.get("message") or {}).get("content")) or ""
        top: List[Tuple[str, float]] = []
        content = ((choice.get("logprobs") or {}).get("content")) or []
        if content:
            for alt in content[0].get("top_logprobs") or []:
                tok = alt.get("token")
                lp = alt.get("logprob")
                if tok is None or lp is None:
                    continue
                top.append((str(tok), float(lp)))
            top.sort(key=lambda t: t[1], reverse=True)
        return FirstToken(text=text, top=top)
