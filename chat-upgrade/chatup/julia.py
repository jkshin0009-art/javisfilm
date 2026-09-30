"""Julia-1 as a drop-in decider, and a cascade that asks the LLM only when Julia is unsure.

Julia-1 (SupersonicLabs, Apache-2.0) is a 144M text decision model: state + question
+ options in, one probability per option out, in tens of milliseconds on the CPU.
The project already serves it with tools/julia_router.py --serve:

    POST http://127.0.0.1:5691/predict  {"state", "question", "options"}
      -> {"probabilities": [p per option, same order]}

JuliaDecider has the same decide(state, q) as Decider and returns the same Decision,
so ConversationJudge, JudgeBridge and any checker can switch to it without other
changes. It reads text only: a question that comes with images gets level "none",
and the caller falls back to its rule (or the cascade sends it to the LLM).

CascadeDecider is the System 1 / System 2 split the project's agent_choose uses:
Julia answers first; when its top probability is under `trust`, the LLM Decider is
asked and its answer is used. Most decisions then cost Julia's time, and only the
unsure ones pay for the LLM.
"""
from __future__ import annotations

import json
import math
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Dict, List, Optional, Sequence, Union

from chatup.decide import Decision, Question
from chatup.llm import LLMError

DEFAULT_URL = "http://127.0.0.1:5691"
MAX_OPTIONS = 20            # Julia-1 reads 2 to 20 options
OPTION_CHARS = 300          # julia_router cuts longer options

# How a yes/no question is put to Julia: a two-option choice. The Decision keeps
# the Yes/No names every caller already reads.
NOUL_TEXT = {"Yes": "Yes (그렇다)", "No": "No (아니다)"}


class JuliaError(LLMError):
    """Julia server unreachable or its answer unreadable. A subclass of LLMError so
    code that already guards LLM calls also guards these."""


class JuliaClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = 5.0) -> None:
        self.base = base_url.rstrip("/")
        if self.base.endswith("/predict"):
            self.base = self.base[: -len("/predict")]
        self.timeout = timeout

    def probabilities(self, state: str, question: str, options: Sequence[str]) -> List[float]:
        body = {"state": state, "question": question, "options": list(options)}
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base + "/predict", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                reply = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            raise JuliaError(f"HTTP {e.code} from {self.base}: {detail}") from None
        except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
            raise JuliaError(f"cannot reach {self.base}: {e}") from None
        except ValueError as e:
            raise JuliaError(f"bad JSON from {self.base}: {e}") from None
        probs = reply.get("probabilities") if isinstance(reply, dict) else None
        if isinstance(probs, dict):                     # {option: p}, in case the router keys them
            probs = [probs.get(o) for o in options]
        if not isinstance(probs, list) or len(probs) != len(options):
            raise JuliaError(f"expected {len(options)} probabilities, got {str(reply)[:200]}")
        try:
            vals = [max(0.0, float(p)) for p in probs]
        except (TypeError, ValueError):
            raise JuliaError(f"non-numeric probabilities: {str(probs)[:200]}") from None
        total = sum(vals)
        if not total > 0 or math.isnan(total):
            raise JuliaError("probabilities sum to zero")
        return [v / total for v in vals]

    def health(self) -> bool:
        try:
            with urllib.request.urlopen(self.base + "/health", timeout=self.timeout) as r:
                return r.status == 200
        except Exception:
            return False


class _Log:
    def __init__(self, path: Optional[str], state_chars: int) -> None:
        self.path = path
        self.state_chars = state_chars
        self.lock = threading.Lock()
        self.counter = 0

    def next_id(self) -> str:
        with self.lock:
            self.counter += 1
            return f"{int(time.time())}-{self.counter}"

    def write(self, state: str, dec: Decision) -> Decision:
        if not self.path:
            return dec
        rec = asdict(dec)
        rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        rec["state"] = state[-self.state_chars:] if state else ""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            with self.lock, open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return dec


class JuliaDecider:
    """orders: 2 (default) asks once as listed and once reversed and averages in log
    space, so a preference for the first or last option cancels out; 1 asks once.
    Julia answers in tens of milliseconds, so the second order costs little."""

    def __init__(self, client: Optional[JuliaClient] = None, *, orders: int = 2,
                 log_path: Optional[str] = None, state_chars_in_log: int = 1500) -> None:
        self.client = client or JuliaClient()
        self.orders = 1 if orders == 1 else 2
        self._log = _Log(log_path, state_chars_in_log)

    def _texts(self, q: Question) -> List[str]:
        if q.kind == "noul":
            return [NOUL_TEXT[o] for o in q.options]
        return [o[:OPTION_CHARS] for o in q.options]

    def decide(self, state: str, q: Question, images: Sequence[str] = ()) -> Decision:
        t0 = time.perf_counter()
        did = self._log.next_id()
        if images:
            return self._none(state, q, t0, did, 0, "julia reads text only; the question came with images")
        if q.k > MAX_OPTIONS:
            return self._none(state, q, t0, did, 0, f"julia reads at most {MAX_OPTIONS} options")
        texts = self._texts(q)
        perms = [list(range(q.k))]
        if self.orders == 2:
            perms.append(list(reversed(range(q.k))))
        rows: List[List[float]] = []
        for perm in perms:
            probs = self.client.probabilities(state or "(empty)", q.text, [texts[i] for i in perm])
            row = [0.0] * q.k
            for j, i in enumerate(perm):
                row[i] = probs[j]
            rows.append(row)
        z = [sum(math.log(max(r[i], 1e-12)) for r in rows) / len(rows) for i in range(q.k)]
        m = max(z)
        ex = [math.exp(x - m) for x in z]
        s = sum(ex)
        dist = [e / s for e in ex]
        ranked = sorted(range(q.k), key=lambda i: dist[i], reverse=True)
        top = ranked[0]
        winners = [max(range(q.k), key=lambda i: r[i]) for r in rows]
        dec = Decision(q.id, q.kind, list(q.options), {o: round(p, 6) for o, p in zip(q.options, dist)},
                       q.options[top], dist[top], dist[top] - dist[ranked[1]], "julia", 1.0,
                       sum(1 for w in winners if w != top) / len(winners), len(perms),
                       (time.perf_counter() - t0) * 1000.0,
                       value=sum(i * p for i, p in enumerate(dist)) if q.kind == "score" else None, id=did)
        return self._log.write(state, dec)

    def _none(self, state, q, t0, did, calls, note) -> Decision:
        dec = Decision(q.id, q.kind, list(q.options), {o: 0.0 for o in q.options}, None, None, None,
                       "none", 0.0, 0.0, calls, (time.perf_counter() - t0) * 1000.0, note=note, id=did)
        return self._log.write(state, dec)


class CascadeDecider:
    """Julia first; the LLM decider when Julia is not sure (top p < trust), when the
    question has images, or when Julia is down. If the LLM fails too, Julia's own
    answer comes back (it may still be under the caller's threshold)."""

    def __init__(self, first: JuliaDecider, second, *, trust: float = 0.9) -> None:
        self.first = first
        self.second = second
        self.trust = trust

    def decide(self, state: str, q: Question, images: Sequence[str] = ()) -> Decision:
        t0 = time.perf_counter()
        d1: Optional[Decision] = None
        why = ""
        try:
            d1 = self.first.decide(state, q, images)
        except LLMError as e:
            why = f"julia failed ({str(e)[:80]})"
        if d1 is not None:
            if d1.confidence is not None and d1.confidence >= self.trust:
                return d1
            p1 = "-" if d1.confidence is None else f"{d1.confidence:.2f}"
            why = d1.note or f"julia p={p1} < trust {self.trust}"
        try:
            d2 = self.second.decide(state, q, images)
        except LLMError:
            if d1 is None:
                raise
            return d1
        d2.note = ("; ".join(x for x in (d2.note, "asked llm: " + why) if x))[:300]
        d2.calls += d1.calls if d1 is not None else 0
        d2.ms = (time.perf_counter() - t0) * 1000.0
        return d2


def make_decider(backend: str, llm_decider=None, *, julia_url: str = DEFAULT_URL, timeout: float = 5.0,
                 trust: float = 0.9, log_path: Optional[str] = None,
                 julia_client: Optional[JuliaClient] = None) -> Union[JuliaDecider, CascadeDecider, object]:
    """backend: "llm" (llm_decider as is), "julia", or "cascade" (julia, then llm when unsure)."""
    backend = (backend or "llm").strip().lower()
    if backend == "llm":
        if llm_decider is None:
            raise ValueError("backend llm needs an llm decider")
        return llm_decider
    julia = JuliaDecider(julia_client or JuliaClient(julia_url, timeout), log_path=log_path)
    if backend == "julia":
        return julia
    if backend == "cascade":
        if llm_decider is None:
            raise ValueError("backend cascade needs an llm decider")
        return CascadeDecider(julia, llm_decider, trust=trust)
    raise ValueError(f"unknown backend {backend!r} (llm | julia | cascade)")
