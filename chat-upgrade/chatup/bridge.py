"""JudgeBridge: the one object the project imports to put Jev-style judgments
behind switches, without changing what the project does until a switch says so.

Every hook takes the project's own answer (the baseline) and returns the answer
to use:

  "off"      the baseline; nothing is asked
  "observe"  the baseline; the judgment runs on a background thread and is logged
             next to the baseline, so a session shows where the judge would differ
  "act"      the judge's answer when it is confident, else the baseline

Errors and timeouts return the baseline. The hook log holds no conversation text,
only which hook, the two answers, the probability and the time taken.

Modes come from the environment (FJ_JUDGE for all hooks, FJ_JUDGE_<HOOK> for one)
and from an optional JSON file that is re-read when it changes, so a mode can be
switched while the app runs:  {"default": "observe", "image": "act"}
"""
from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Callable, Dict, Iterable, List, Optional, Sequence

from chatup.decide import Decider
from chatup.judge import EVERYONE, ConversationJudge, Line, Verdict
from chatup.llm import LLMClient
from chatup.shaper import ThinkFilter

HOOKS = ("think", "image", "autonomy", "speaker", "addressed", "stuck")
MODES = ("off", "observe", "act")


def to_lines(history: Iterable, user_name: str = "사용자") -> List[Line]:
    """Accepts Line objects, (speaker, text) pairs, or dicts with speaker/name/role
    and text/content keys. A role of "user" becomes user_name."""
    out: List[Line] = []
    for item in history:
        if isinstance(item, Line):
            out.append(item)
            continue
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            out.append(Line(str(item[0]), str(item[1])))
            continue
        if isinstance(item, dict):
            who = item.get("speaker") or item.get("name") or item.get("persona") or item.get("role") or "?"
            if who == "user":
                who = user_name
            text = item.get("text") if item.get("text") is not None else item.get("content", "")
            if isinstance(text, str) and text.strip():
                out.append(Line(str(who), text))
    return out


class JudgeBridge:
    def __init__(self, base_url: str, modes=None, *, roster: str = "", user_name: str = "사용자",
                 thresholds: Optional[Dict[str, float]] = None, log_dir: Optional[str] = None,
                 modes_file: Optional[str] = None, timeout: float = 6.0, max_lines: int = 10,
                 parallel: int = 1, max_pending: int = 4, log_states: bool = False,
                 client=None) -> None:
        self.client = client or LLMClient(base_url, timeout=timeout)
        state_log = os.path.join(log_dir, "decisions.jsonl") if (log_dir and log_states) else None
        self.judge = ConversationJudge(Decider(self.client, parallel=parallel, log_path=state_log),
                                       roster=roster, user_name=user_name, thresholds=thresholds,
                                       max_lines=max_lines)
        self.user_name = user_name
        self.timeout = timeout
        self.max_pending = max_pending
        self.log_path = os.path.join(log_dir, "hooks.jsonl") if log_dir else None
        self._modes = self._parse_modes(modes)
        self.modes_file = modes_file
        self._file_mtime = None
        self._file_modes: Dict[str, str] = {}
        self._file_checked = 0.0
        self._lock = threading.Lock()
        self._pending = 0
        self._observe_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="judge-observe")
        self._act_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="judge-act")

    # ------------------------------------------------------------ construction
    @classmethod
    def from_env(cls, base_url: str, env=None, **kw) -> "JudgeBridge":
        env = os.environ if env is None else env
        modes = {"default": env.get("FJ_JUDGE", "off")}
        for hook in HOOKS:
            v = env.get("FJ_JUDGE_" + hook.upper())
            if v:
                modes[hook] = v
        kw.setdefault("log_dir", env.get("FJ_JUDGE_LOG") or None)
        kw.setdefault("modes_file", env.get("FJ_JUDGE_FILE") or None)
        if env.get("FJ_JUDGE_TIMEOUT"):
            kw.setdefault("timeout", float(env["FJ_JUDGE_TIMEOUT"]))
        return cls(base_url, modes, **kw)

    @staticmethod
    def _parse_modes(modes) -> Dict[str, str]:
        if modes is None:
            return {"default": "off"}
        if isinstance(modes, str):
            modes = {"default": modes}
        out = {}
        for k, v in dict(modes).items():
            v = str(v).strip().lower()
            if v in MODES:
                out[str(k).strip().lower()] = v
        out.setdefault("default", "off")
        return out

    def _read_file(self) -> None:
        if not self.modes_file:
            return
        now = time.monotonic()
        if now - self._file_checked < 2.0:
            return
        self._file_checked = now
        try:
            mtime = os.path.getmtime(self.modes_file)
        except OSError:
            self._file_modes, self._file_mtime = {}, None
            return
        if mtime == self._file_mtime:
            return
        try:
            with open(self.modes_file, encoding="utf-8-sig") as f:
                self._file_modes = self._parse_modes(json.load(f))
        except (OSError, ValueError):
            self._file_modes = {}
        self._file_mtime = mtime

    def mode(self, hook: str) -> str:
        self._read_file()
        for src in (self._file_modes, self._modes):
            if hook in src:
                return src[hook]
        return self._file_modes.get("default") or self._modes.get("default", "off")

    # ------------------------------------------------------------ hooks
    def think_filter(self, assume_open: bool = False) -> ThinkFilter:
        return ThinkFilter(assume_open)

    def image(self, history, baseline: bool) -> bool:
        """Keyword trigger matched (baseline True): is it really a picture request?"""
        lines = to_lines(history, self.user_name)
        return self._run("image", baseline, lambda: self.judge.wants_image(lines),
                         lambda v: None if v.value is None else v.value == "Yes")

    def autonomy(self, history, baseline: bool = True, idle_seconds: float = 0.0) -> bool:
        """Before an autonomous beat: speak now (True) or wait for the user (False)."""
        lines = to_lines(history, self.user_name)
        return self._run("autonomy", baseline, lambda: self.judge.should_speak(lines, idle_seconds),
                         lambda v: None if v.value is None else v.value == "Yes")

    def speaker(self, history, candidates: Sequence[str], baseline: str) -> str:
        cands = list(dict.fromkeys(candidates))
        if len(cands) < 2:
            return baseline
        lines = to_lines(history, self.user_name)
        return self._run("speaker", baseline, lambda: self.judge.next_speaker(lines, cands),
                         lambda v: v.value if v.value in cands else None)

    def addressed(self, history, candidates: Sequence[str], baseline: Optional[str] = None) -> Optional[str]:
        """Whom the user's last line is for. EVERYONE keeps the baseline."""
        cands = list(dict.fromkeys(candidates))
        if not cands:
            return baseline
        lines = to_lines(history, self.user_name)
        return self._run("addressed", baseline, lambda: self.judge.addressed(lines, cands),
                         lambda v: v.value if v.value in cands else None)

    def stuck(self, history, baseline: bool = False) -> bool:
        lines = to_lines(history, self.user_name)
        return self._run("stuck", baseline, lambda: self.judge.stuck(lines),
                         lambda v: None if v.value is None else v.value == "Yes")

    # ------------------------------------------------------------ machinery
    def _run(self, hook: str, baseline, ask: Callable[[], Verdict], to_value: Callable[[Verdict], object]):
        mode = self.mode(hook)
        if mode == "off":
            return baseline
        if mode == "observe":
            with self._lock:
                busy = self._pending >= self.max_pending
                if not busy:
                    self._pending += 1
            if busy:
                self._log(hook, mode, baseline, None, None, baseline, 0.0, error="skipped: busy")
            else:
                self._observe_pool.submit(self._observe, hook, baseline, ask, to_value)
            return baseline
        t0 = time.perf_counter()
        fut = self._act_pool.submit(ask)
        try:
            v = fut.result(timeout=self.timeout)
        except FutureTimeout:
            self._log(hook, mode, baseline, None, None, baseline, _ms(t0), error="timeout")
            return baseline
        except Exception as e:                      # judge trouble must never break the chat
            self._log(hook, mode, baseline, None, None, baseline, _ms(t0), error=_err(e))
            return baseline
        value = to_value(v)
        final = baseline if value is None else value
        self._log(hook, mode, baseline, v, value, final, _ms(t0))
        return final

    def _observe(self, hook, baseline, ask, to_value) -> None:
        t0 = time.perf_counter()
        try:
            v = ask()
            self._log(hook, "observe", baseline, v, to_value(v), baseline, _ms(t0))
        except Exception as e:
            self._log(hook, "observe", baseline, None, None, baseline, _ms(t0), error=_err(e))
        finally:
            with self._lock:
                self._pending -= 1

    def _log(self, hook, mode, baseline, v: Optional[Verdict], value, final, ms, error: str = "") -> None:
        if not self.log_path:
            return
        d = v.decision if v is not None else None
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "hook": hook, "mode": mode,
            "baseline": baseline, "judge": d.answer if d else None, "value": value, "final": final,
            "changed": final != baseline, "p": round(d.confidence, 4) if d and d.confidence is not None else None,
            "level": d.level if d else None, "calls": d.calls if d else 0, "ms": round(ms, 1),
        }
        if error:
            rec["error"] = error
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
            with self._lock, open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def wait_observers(self, timeout: float = 10.0) -> bool:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            with self._lock:
                if self._pending == 0:
                    return True
            time.sleep(0.02)
        return False

    def close(self) -> None:
        self._observe_pool.shutdown(wait=False)
        self._act_pool.shutdown(wait=False)


def _ms(t0: float) -> float:
    return (time.perf_counter() - t0) * 1000.0


def _err(e: Exception) -> str:
    return f"{type(e).__name__}: {str(e)[:200]}"


# ---------------------------------------------------------------- log summary
def summarize(log_path: str) -> str:
    """Markdown summary of a hooks.jsonl: counts, agreement with the baseline,
    confidence and time per hook. Carries no names and no conversation text."""
    rows = []
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    pass
    out = [f"# judge hooks summary", "", f"- log: {os.path.basename(log_path)}", f"- records: {len(rows)}"]
    if rows:
        out.append(f"- from {rows[0].get('ts')} to {rows[-1].get('ts')}")
    out += ["", "| hook | mode | n | decided | agree with baseline | unsure | changed | errors | "
                "p median | ms median | ms p90 | ms max |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    keys = sorted({(r.get("hook"), r.get("mode")) for r in rows}, key=lambda k: (HOOKS.index(k[0])
                                                                                 if k[0] in HOOKS else 99, k[1]))
    for hook, mode in keys:
        rs = [r for r in rows if r.get("hook") == hook and r.get("mode") == mode]
        errs = [r for r in rs if r.get("error")]
        ok = [r for r in rs if not r.get("error")]
        decided = [r for r in ok if r.get("value") is not None]
        agree = sum(1 for r in decided if r.get("value") == r.get("baseline"))
        unsure = len(ok) - len(decided)
        changed = sum(1 for r in rs if r.get("changed"))
        ps = sorted(r["p"] for r in ok if r.get("p") is not None)
        ms = sorted(r.get("ms", 0.0) for r in ok)
        pct = f"{agree}/{len(decided)} ({100.0 * agree / len(decided):.0f}%)" if decided else "-"
        out.append(f"| {hook} | {mode} | {len(rs)} | {len(decided)} | {pct} | {unsure} | {changed} | "
                   f"{len(errs)} | {_q(ps, 0.5, '.2f')} | {_q(ms, 0.5, '.0f')} | {_q(ms, 0.9, '.0f')} | "
                   f"{(f'{ms[-1]:.0f}' if ms else '-')} |")
    kinds: Dict[str, int] = {}
    for r in rows:
        if r.get("error"):
            k = r["error"].split(":")[0]
            kinds[k] = kinds.get(k, 0) + 1
    if kinds:
        out += ["", "errors: " + ", ".join(f"{k} x{n}" for k, n in sorted(kinds.items()))]
    return "\n".join(out) + "\n"


def _q(vals: List[float], q: float, fmt: str) -> str:
    if not vals:
        return "-"
    return format(vals[min(len(vals) - 1, int(q * len(vals)))], fmt)
