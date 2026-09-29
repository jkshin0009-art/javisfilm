"""Jev-style typed decisions read from the chatbot's own LLM.

Jev (TypeSafe AI) is a "System One" model: it takes a state and a typed question
(choice, yes/no, score) and returns a decision with a probability instead of
text. AnyJev (nokia-applied-research/AnyJev, Apache-2.0) showed the same can be
read from any open LLM without training: ask the question, generate nothing, and
read the next-token probabilities of the answer labels (A/B/C..., Yes/No, 1..5).
This module is a small, dependency-free port of AnyJev's zero-label level (L0)
for llama-server:

  * the options are shown in several cyclic orders and the per-option
    log-probabilities are averaged, so the model's preference for "A" or for
    whatever is listed first cancels out (AnyJev's order-flip rate 0.230 -> 0.073);
  * for choice questions a running label prior, estimated from past decisions
    without labels, is divided out;
  * "adaptive" reads the orders one at a time and stops as soon as the leader is
    clear, so an easy decision costs two short prefills.

The caller gets a Decision with a distribution and a confidence, and code decides
what to do with it: act above a threshold, fall back to a plain rule below it.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import string
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Sequence, Tuple, Union

from chatup.llm import with_images

LETTERS = string.ascii_uppercase
MAX_OPTIONS = 12

DEFAULT_SYSTEM = (
    "You are a decision function. You will be given a state and one question. "
    "Reply with the answer label only: no words, no punctuation, no explanation."
)

# Tokens a model may produce for Yes/No when the state is Korean.
_YES = {"yes", "y", "예", "네", "응"}
_NO = {"no", "n", "아니", "아니오", "아니요", "아뇨"}


class QuestionError(ValueError):
    pass


@dataclass(frozen=True)
class Question:
    """A typed question. Build with Question.choice / .noul / .score."""

    kind: str                 # "choice" | "noul" | "score"
    text: str
    options: Tuple[str, ...]
    name: str = ""

    @staticmethod
    def choice(text: str, options: Sequence[str], name: str = "") -> "Question":
        opts = tuple(str(o) for o in options)
        if len(opts) < 2:
            raise QuestionError("choice needs at least 2 options")
        if len(opts) > MAX_OPTIONS:
            raise QuestionError(f"choice supports at most {MAX_OPTIONS} options")
        if len(set(opts)) != len(opts):
            raise QuestionError("choice options must be unique")
        return Question("choice", text, opts, name)

    @staticmethod
    def noul(text: str, name: str = "") -> "Question":
        return Question("noul", text, ("Yes", "No"), name)

    @staticmethod
    def score(text: str, levels: Sequence[str], name: str = "") -> "Question":
        """Ordered levels, lowest first. The value is the level index (0..n-1)."""
        lv = tuple(str(x) for x in levels)
        if not 2 <= len(lv) <= 9:
            raise QuestionError("score supports 2 to 9 levels")
        return Question("score", text, lv, name)

    @property
    def k(self) -> int:
        return len(self.options)

    @property
    def id(self) -> str:
        if self.name:
            return self.name
        h = hashlib.sha256((self.kind + self.text + "|".join(self.options)).encode("utf-8"))
        return "q_" + h.hexdigest()[:8]

    def labels(self) -> List[str]:
        if self.kind == "noul":
            return ["Yes", "No"]
        if self.kind == "score":
            return [str(i + 1) for i in range(self.k)]
        return list(LETTERS[: self.k])


@dataclass
class Decision:
    name: str
    kind: str
    options: List[str]
    distribution: Dict[str, float]
    answer: Optional[str]
    confidence: Optional[float]     # probability of `answer`; None when it was parsed from text
    margin: Optional[float]         # top minus runner-up
    level: str                      # "L0" (rotated), "raw" (one order), "parsed" (no logprobs), "none"
    label_mass: float               # smallest share of the next-token mass that fell on the labels
    flips: float                    # share of orders whose winner disagreed with the final answer
    calls: int
    ms: float
    value: Optional[float] = None   # score only: expected level index
    note: str = ""
    id: str = ""

    def p(self, option: str) -> float:
        return self.distribution.get(option, 0.0)

    @property
    def yes(self) -> float:
        """noul only: probability of Yes."""
        return self.distribution.get("Yes", 0.0)

    def accept(self, threshold: float, allow_parsed: bool = False) -> Optional[str]:
        """The answer when it is safe to act on it, else None."""
        if self.answer is None:
            return None
        if self.confidence is None:
            return self.answer if allow_parsed else None
        return self.answer if self.confidence >= threshold else None


# ---------------------------------------------------------------- orders
def cyclic_shifts(k: int) -> List[List[int]]:
    """perm[j] = index of the option shown at position j."""
    return [[(j + s) % k for j in range(k)] for s in range(k)]


def spread_order(k: int) -> List[int]:
    """Shift indices in an order that spreads positions early: 0, k/2, k/4, 3k/4, ..."""
    order, seen, d = [0], {0}, 2
    while len(order) < k and d <= 4 * k:
        for num in range(1, d, 2):
            s = int(k * num / d) % k
            if s not in seen:
                seen.add(s)
                order.append(s)
        d *= 2
    order.extend(s for s in range(k) if s not in seen)
    return order[:k]


def build_user(state: str, q: Question, perm: Sequence[int]) -> str:
    labels = q.labels()
    lines = ["State:", state.strip() if state and state.strip() else "(empty)", "", f"Question: {q.text}"]
    if q.kind == "noul":
        order = [labels[i] for i in perm]
        lines.append(f"Answer {order[0]} or {order[1]}.")
    elif q.kind == "score":
        lines.append("Pick the level that applies (the levels are ordered):")
        for j, i in enumerate(perm):
            lines.append(f"{labels[j]}. {q.options[i]}")
        lines.append("Answer with the number only.")
    else:
        lines.append("Options:")
        for j, i in enumerate(perm):
            lines.append(f"{labels[j]}. {q.options[i]}")
        lines.append("Answer with the letter only.")
    return "\n".join(lines)


# ---------------------------------------------------------------- readout
def _logsumexp(xs: Sequence[float]) -> float:
    m = max(xs)
    return m + math.log(sum(math.exp(x - m) for x in xs))


def _normalise_token(tok: str) -> str:
    return tok.strip().strip(".:)*\"'`").strip()


def _label_of(tok: str, q: Question) -> Optional[str]:
    t = _normalise_token(tok)
    if not t:
        return None
    if q.kind == "noul":
        low = t.lower()
        if low in _YES:
            return "Yes"
        if low in _NO:
            return "No"
        return None
    labels = q.labels()
    return t if t in labels else None


def read_labels(top: Sequence[Tuple[str, float]], q: Question) -> Tuple[List[float], float, int]:
    """Map top-N (token, logprob) onto the question's labels.

    Several tokens can spell one label ("A" and " A"); their probabilities add.
    A label missing from the top-N list gets half the smallest listed probability,
    an upper bound that keeps it possible but never favoured.
    Returns (logprob per label in label order, label mass, labels found)."""
    labels = q.labels()
    found: Dict[str, List[float]] = {}
    for tok, lp in top:
        lab = _label_of(tok, q)
        if lab is not None:
            found.setdefault(lab, []).append(lp)
    floor = (min(lp for _, lp in top) if top else -30.0) + math.log(0.5)
    out = []
    mass = 0.0
    for lab in labels:
        if lab in found:
            lp = _logsumexp(found[lab])
            mass += math.exp(lp)
            out.append(lp)
        else:
            out.append(floor)
    return out, mass, len(found)


def _softmax(lps: Sequence[float]) -> List[float]:
    m = max(lps)
    ex = [math.exp(x - m) for x in lps]
    s = sum(ex)
    return [e / s for e in ex]


def _combine_logmean(per_option: List[List[float]]) -> List[float]:
    """per_option: [orders][K] probabilities in option space -> geometric mean, renormalised."""
    k = len(per_option[0])
    z = [sum(math.log(max(row[i], 1e-12)) for row in per_option) / len(per_option) for i in range(k)]
    return _softmax(z)


def _parse_text(text: str, q: Question) -> Optional[str]:
    t = text.strip()
    if not t:
        return None
    first = t.split()[0]
    lab = _label_of(first, q)
    if lab is None and q.kind != "noul":
        lab = _label_of(first[:1], q)
    return lab


# ---------------------------------------------------------------- decider
class Decider:
    """client: an LLMClient (or anything with first_token_logprobs(messages, top_n)).

    rotations: "adaptive" (default), "full", or an int number of orders.
    stop_p:    adaptive stops once the running winner has at least this probability.
    min_label_mass: an order whose labels hold less of the next-token mass than this
               is treated as no signal (thinking left on, the model starting with
               "**", a template that eats the answer).
    parallel:  orders sent at once. llama-server with -np 2 or more answers them in
               the same batch, so two orders cost about the time of one."""

    def __init__(self, client, *, rotations: Union[str, int] = "adaptive", top_n: int = 20,
                 stop_p: float = 0.85, min_label_mass: float = 0.3, prior_correction: bool = True,
                 min_prior_n: int = 8, system: str = DEFAULT_SYSTEM,
                 log_path: Optional[str] = None, state_chars_in_log: int = 1500,
                 parallel: int = 2) -> None:
        self.client = client
        self.rotations = rotations
        self.top_n = top_n
        self.stop_p = stop_p
        self.min_label_mass = min_label_mass
        self.prior_correction = prior_correction
        self.min_prior_n = min_prior_n
        self.system = system
        self.log_path = log_path
        self.state_chars_in_log = state_chars_in_log
        self._prior: Dict[Tuple[str, int], Tuple[List[float], int]] = {}
        self._lock = threading.Lock()
        self._counter = 0
        self.parallel = max(1, int(parallel))
        self._pool: Optional[ThreadPoolExecutor] = None

    # ---------------- prior (choice only: position preference, not answer base rate)
    def _prior_for(self, q: Question) -> Optional[List[float]]:
        if not self.prior_correction or q.kind != "choice":
            return None
        with self._lock:
            entry = self._prior.get((q.id, q.k))
        if entry is None or entry[1] < self.min_prior_n:
            return None
        return entry[0]

    def _update_prior(self, q: Question, rows: List[List[float]]) -> None:
        if not self.prior_correction or q.kind != "choice" or not rows:
            return
        with self._lock:
            mean, n = self._prior.get((q.id, q.k), ([1.0 / q.k] * q.k, 0))
            for row in rows:
                n += 1
                mean = [m + (r - m) / n for m, r in zip(mean, row)]
            self._prior[(q.id, q.k)] = (mean, n)

    # ---------------- orders
    def _orders(self, q: Question) -> List[List[int]]:
        if q.kind == "score":
            return [list(range(q.k))]
        if q.kind == "noul":
            both = [[0, 1], [1, 0]]
            return both[:1] if self.rotations == 1 else both
        shifts = cyclic_shifts(q.k)
        order = [shifts[s] for s in spread_order(q.k)]
        if isinstance(self.rotations, int):
            return order[: max(1, min(q.k, self.rotations))]
        return order

    def _ask(self, state: str, q: Question, perm: Sequence[int], images: Sequence[str] = ()):
        messages = [{"role": "system", "content": self.system},
                    {"role": "user", "content": with_images(build_user(state, q, perm), images)}]
        return self.client.first_token_logprobs(messages, top_n=self.top_n)

    def _ask_many(self, state: str, q: Question, perms: List[List[int]], images: Sequence[str] = ()):
        if len(perms) == 1:
            return [self._ask(state, q, perms[0], images)]
        with self._lock:
            if self._pool is None:
                self._pool = ThreadPoolExecutor(max_workers=self.parallel, thread_name_prefix="decide")
            pool = self._pool
        return list(pool.map(lambda perm: self._ask(state, q, perm, images), perms))

    def decide(self, state: str, q: Question, images: Sequence[str] = ()) -> Decision:
        """images: paths shown to a vision model before the question (needs --mmproj)."""
        t0 = time.perf_counter()
        orders = self._orders(q)
        adaptive = self.rotations == "adaptive" and q.kind == "choice"
        prior = self._prior_for(q)
        per_option: List[List[float]] = []
        raw_rows: List[List[float]] = []
        winners: List[int] = []
        masses: List[float] = []
        calls = 0
        parsed: Optional[str] = None
        dist: Optional[List[float]] = None

        pending = list(orders)
        stop = False
        while pending and not stop:
            batch, pending = pending[: self.parallel], pending[self.parallel:]
            answers = self._ask_many(state, q, batch, images)
            calls += len(batch)
            for perm, ft in zip(batch, answers):
                if not ft.has_logprobs:
                    parsed = _parse_text(ft.text, q)
                    stop = True
                    break
                lps, mass, _ = read_labels(ft.top, q)
                masses.append(mass)
                if mass < self.min_label_mass:
                    continue
                pos = _softmax(lps)              # indexed by label position
                raw_rows.append(pos)
                if prior is not None:
                    adj = [p / max(pr, 1e-6) for p, pr in zip(pos, prior)]
                    total = sum(adj)
                    pos = [a / total for a in adj]
                if q.kind == "noul":
                    opt = pos                    # Yes/No labels stay attached to their meaning
                else:
                    opt = [0.0] * q.k
                    for j, i in enumerate(perm):
                        opt[i] = pos[j]
                per_option.append(opt)
                winners.append(max(range(q.k), key=lambda i: opt[i]))
                dist = _combine_logmean(per_option)
                if adaptive and len(per_option) >= 2:
                    lead = max(range(q.k), key=lambda i: dist[i])
                    if dist[lead] >= self.stop_p and winners[-1] == winners[-2] == lead:
                        stop = True
                        break

        ms = (time.perf_counter() - t0) * 1000.0
        self._counter += 1
        did = f"{int(time.time())}-{self._counter}"
        if parsed is not None or (dist is None and not masses):
            dec = Decision(q.id, q.kind, list(q.options),
                           {o: (1.0 if parsed is not None and lab == parsed else 0.0)
                            for o, lab in zip(q.options, q.labels())},
                           None, None, None, "parsed" if parsed else "none", 0.0, 0.0, calls, ms,
                           note="server returned no logprobs", id=did)
            if parsed is not None:
                dec.answer = q.options[q.labels().index(parsed)]
            return self._log(state, dec)
        if dist is None:
            dec = Decision(q.id, q.kind, list(q.options), {o: 0.0 for o in q.options},
                           None, None, None, "none", min(masses), 0.0, calls, ms,
                           note="labels got too little probability; is thinking switched off?", id=did)
            return self._log(state, dec)

        self._update_prior(q, raw_rows)
        order_idx = sorted(range(q.k), key=lambda i: dist[i], reverse=True)
        top = order_idx[0]
        margin = dist[top] - (dist[order_idx[1]] if q.k > 1 else 0.0)
        flips = sum(1 for w in winners if w != top) / len(winners)
        value = sum(i * p for i, p in enumerate(dist)) if q.kind == "score" else None
        level = "L0" if len(per_option) > 1 else "raw"
        dec = Decision(q.id, q.kind, list(q.options), {o: round(p, 6) for o, p in zip(q.options, dist)},
                       q.options[top], dist[top], margin, level, min(masses), flips, calls, ms,
                       value=value, id=did)
        return self._log(state, dec)

    def _log(self, state: str, dec: Decision) -> Decision:
        if not self.log_path:
            return dec
        rec = asdict(dec)
        rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        rec["state"] = state[-self.state_chars_in_log:] if state else ""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
            with self._lock, open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return dec
