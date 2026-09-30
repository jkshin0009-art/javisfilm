"""python -m chatup probe|chat|voices ...

probe   measure Jev-style decisions on the chatbot's LLM: do logprobs come back,
        is thinking really off (label mass), how long a decision takes, and
        whether the answers are right on fictional test conversations
chat    terminal run of the reference loop with example characters (text only,
        or with voices when --voices and a TTS engine are given)
voices  check a voice bank folder, optionally render one sample per emotion
report  summarize a JudgeBridge hooks.jsonl (counts, agreement, time; no text)
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import threading
import time
from typing import List

from chatup.decide import Decider
from chatup.julia import DEFAULT_URL as JULIA_URL
from chatup.julia import make_decider
from chatup.judge import EVERYONE, STATE_ONGOING, STATE_WAITING, ConversationJudge, Line
from chatup.llm import LLMClient, LLMError

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ROSTER = "하나: 촬영 감독\n도윤: 시나리오 작가\n미래: 로케이션 담당"
NAMES = ["하나", "도윤", "미래"]


def _utf8_console() -> None:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def L(*pairs) -> List[Line]:
    return [Line(a, b) for a, b in pairs]


def probe_cases():
    """(name, expected, callable(judge) -> Verdict). All conversations are made up."""
    base = L(("사용자", "다음 주 촬영 준비 얘기 좀 하자."),
             ("하나", "조명 장비는 거의 다 챙겼어요."))
    return [
        ("next_speaker: 이름을 불러 물음", "도윤",
         lambda j: j.next_speaker(base + L(("하나", "도윤아, 대본 수정은 어디까지 됐어?")), NAMES)),
        ("next_speaker: 순서를 뒤집어도 같은가", "도윤",
         lambda j: j.next_speaker(base + L(("하나", "도윤아, 대본 수정은 어디까지 됐어?")), NAMES[::-1])),
        ("next_speaker: 장소 질문", "미래",
         lambda j: j.next_speaker(base + L(("도윤", "바닷가 장면 찍을 곳은 정해졌어? 미래 씨가 알아본다고 했잖아요.")), NAMES)),
        ("addressed: 한 사람에게", "하나",
         lambda j: j.addressed(base + L(("사용자", "하나야, 조명 말고 카메라는 뭐 쓸 거야?")), NAMES)),
        ("addressed: 모두에게", EVERYONE,
         lambda j: j.addressed(base + L(("사용자", "다들 오늘 저녁은 뭐 먹을래?")), NAMES)),
        ("should_speak: 사용자에게 질문한 뒤", STATE_WAITING,
         lambda j: j.should_speak(base + L(("도윤", "그래서, 결말은 열린 결말이 좋으세요, 닫힌 결말이 좋으세요?")), 12)),
        ("should_speak: 의논 중 잠시 멈춤", STATE_ONGOING,
         lambda j: j.should_speak(base + L(("미래", "바닷가 후보지가 두 군데 있는데요,"),
                                           ("도윤", "둘 다 장단점이 있어서 아직 못 골랐어요.")), 12)),
        ("wants_stop: 조용히 해 달라", "Yes",
         lambda j: j.wants_stop(base + L(("사용자", "잠깐만, 다들 조용히 좀 해 줘. 전화 받아야 해.")))),
        ("wants_stop: 계속하라", "No",
         lambda j: j.wants_stop(base + L(("사용자", "좋아, 그 얘기 계속해 봐.")))),
        ("stuck: 같은 말 반복", "Yes",
         lambda j: j.stuck(L(("하나", "그래, 맞아."), ("도윤", "응, 맞아 맞아."), ("미래", "그러니까, 맞아."),
                             ("하나", "그래, 맞는 말이야."), ("도윤", "응, 맞아."), ("미래", "맞아, 그래.")))),
        ("stuck: 진행 중인 대화", "No",
         lambda j: j.stuck(base + L(("미래", "바닷가 후보지는 강릉과 태안이에요."),
                                    ("도윤", "그럼 강릉 쪽으로 대본의 새벽 장면을 옮길게요.")))),
        ("wants_image: 그림을 그려 달라", "Yes",
         lambda j: j.wants_image(base + L(("사용자", "방금 말한 새벽 바닷가 장면, 그림으로 한번 그려 줘.")))),
        ("wants_image: '장면'이 들어간 질문", "No",
         lambda j: j.wants_image(base + L(("사용자", "3번 장면에서 도윤이는 왜 화를 낸 거야?")))),
        ("wants_image: '보여'가 들어간 부탁", "No",
         lambda j: j.wants_image(base + L(("사용자", "아까 고친 대사 한 번만 다시 보여 줘.")))),
        ("route: 그림 요청", "지금 이야기하는 장면을 이미지로 만든다",
         lambda j: j.route(base + L(("사용자", "방금 말한 새벽 바닷가 장면, 어떤 느낌인지 그림으로 한번 보여 줘.")))),
        ("route: 잡담", "대화를 그대로 이어간다",
         lambda j: j.route(base + L(("사용자", "하나야, 오늘 점심은 먹었어?")))),
        ("emotion: 기쁜 소식", "happy",
         lambda j: j.emotion("하나", "정말? 우리 영화제 본선에 올랐다고? 너무 잘됐다!", ["neutral", "happy", "sad", "angry"])),
        ("emotion: 슬픈 소식", "sad",
         lambda j: j.emotion("도윤", "그 소식 듣고 하루 종일 아무것도 못 했어. 너무 허전하다.", ["neutral", "happy", "sad", "angry"])),
        ("reply_bad: 앞 줄을 그대로 반복", "Yes",
         lambda j: j.reply_bad(base + L(("미래", "바닷가 후보지는 강릉과 태안이에요.")), "도윤",
                               "바닷가 후보지는 강릉과 태안이에요.")),
    ]


ROSTER_EN = "Hana: cinematographer\nDoyun: screenwriter\nMirae: location manager"
NAMES_EN = ["Hana", "Doyun", "Mirae"]
EVERYONE_EN = "Everyone / no one in particular"
WAITING_EN = "A character asked the user something and is waiting for the user's answer"
ONGOING_EN = "The characters were in the middle of a discussion and still have things to say"
STATES_EN = (WAITING_EN, ONGOING_EN, "One topic has wrapped up; it is time to bring up a new one",
             "The user asked everyone to take a break or be quiet")
ACTIONS_EN = ("Keep the conversation going", "Make an image of the scene being discussed",
              "Save the idea just mentioned as a screenplay note", "Ask the user for their opinion")
EMOTIONS = ["neutral", "happy", "sad", "angry"]


def probe_cases_en():
    """The same 19 cases in English, asked straight to the decider. Tells apart
    "the backend cannot judge" from "the backend cannot judge Korean"."""
    from chatup.judge import Verdict, _group_verdict, _noul_verdict
    from chatup.decide import Question

    def state(lines, extra=""):
        body = "\n".join(f"{w}: {t}" for w, t in lines)
        return f"Characters:\n{ROSTER_EN}\n\nRecent conversation:\n{body}" + (f"\n\n{extra}" if extra else "")

    def choice(lines, text, opts, th, extra=""):
        def run(j):
            d = j.decider.decide(state(lines, extra), Question.choice(text, opts))
            return Verdict(d.accept(th), d)
        return run

    def noul(lines, text, th):
        def run(j):
            d = j.decider.decide(state(lines), Question.noul(text))
            return Verdict(_noul_verdict(d, th), d)
        return run

    def conv_state(lines):
        def run(j):
            q = Question.choice("Looking at the recent conversation, pick the state it is in. What matters most "
                                "is whose line came last and how it ended.", STATES_EN)
            d = j.decider.decide(state(lines, "(The user has been silent for 12 seconds.)"), q)
            return Verdict(_group_verdict(d, STATES_EN[1:3], 0.6), d)
        return run

    base = [("User", "Let's talk about getting ready for next week's shoot."),
            ("Hana", "I've packed almost all of the lighting gear.")]
    ask_doyun = base + [("Hana", "Doyun, how far along are the script changes?")]
    nxt = ("Given the flow of the conversation, who would most naturally speak next? Prefer the person who was "
           "asked a question, whose name was called, or who clearly has something to say.")
    addr = "Who was the user's last line meant for?"
    img = ("Is the user's last line a request to draw and show a new picture (image)? Words like 'scene' or "
           "'show' do not make it a picture request.")
    route = "What is the most suitable thing for this chat program to do right now?"
    emo = "Which emotion best fits saying the last line out loud?"
    return [
        ("next_speaker: name called", "Doyun", choice(ask_doyun, nxt, NAMES_EN, 0.55)),
        ("next_speaker: reversed order", "Doyun", choice(ask_doyun, nxt, NAMES_EN[::-1], 0.55)),
        ("next_speaker: location question", "Mirae",
         choice(base + [("Doyun", "Have we picked the beach location? Mirae was going to look into it.")],
                nxt, NAMES_EN, 0.55)),
        ("addressed: one person", "Hana",
         choice(base + [("User", "Hana, besides lighting, which camera are you using?")], addr,
                NAMES_EN + [EVERYONE_EN], 0.6)),
        ("addressed: everyone", EVERYONE_EN,
         choice(base + [("User", "What does everyone want for dinner tonight?")], addr, NAMES_EN + [EVERYONE_EN], 0.6)),
        ("should_speak: after asking the user", WAITING_EN,
         conv_state(base + [("Doyun", "So, would you prefer an open ending or a closed ending?")])),
        ("should_speak: pause in a discussion", ONGOING_EN,
         conv_state(base + [("Mirae", "There are two beach candidates, but"),
                            ("Doyun", "both have pros and cons, so we haven't picked one yet.")])),
        ("wants_stop: be quiet", "Yes",
         noul(base + [("User", "Hold on, everyone be quiet for a second. I need to take a call.")],
              "In their last line, does the user ask to stop the conversation, be quiet, or stop?", 0.8)),
        ("wants_stop: keep going", "No",
         noul(base + [("User", "Good, keep going with that.")],
              "In their last line, does the user ask to stop the conversation, be quiet, or stop?", 0.8)),
        ("stuck: repeating", "Yes",
         noul([("Hana", "Yeah, right."), ("Doyun", "Yes, right, right."), ("Mirae", "I mean, right."),
               ("Hana", "Yeah, that's right."), ("Doyun", "Yes, right."), ("Mirae", "Right, yeah.")],
              "Is the recent conversation repeating itself or going in circles with nothing new?", 0.7)),
        ("stuck: moving along", "No",
         noul(base + [("Mirae", "The beach candidates are Gangneung and Taean."),
                      ("Doyun", "Then I'll move the script's dawn scene to Gangneung.")],
              "Is the recent conversation repeating itself or going in circles with nothing new?", 0.7)),
        ("wants_image: draw it", "Yes",
         noul(base + [("User", "That dawn beach scene you just described, draw it as a picture for me.")], img, 0.8)),
        ("wants_image: 'scene' in a question", "No",
         noul(base + [("User", "In scene 3, why did Doyun get angry?")], img, 0.8)),
        ("wants_image: 'show' in a request", "No",
         noul(base + [("User", "Show me the line you just revised one more time.")], img, 0.8)),
        ("route: picture request", ACTIONS_EN[1],
         choice(base + [("User", "That dawn beach scene you mentioned, show me what it feels like as a picture.")],
                route, ACTIONS_EN, 0.7)),
        ("route: small talk", ACTIONS_EN[0],
         choice(base + [("User", "Hana, did you have lunch today?")], route, ACTIONS_EN, 0.7)),
        ("emotion: good news", "happy",
         choice([("Hana", "Really? Our film made the festival finals? That's wonderful!")], emo, EMOTIONS, 0.5)),
        ("emotion: sad news", "sad",
         choice([("Doyun", "After hearing that, I couldn't do anything all day. I feel so empty.")], emo, EMOTIONS, 0.5)),
        ("reply_bad: repeats the line before", "Yes",
         noul(base + [("Mirae", "The beach candidates are Gangneung and Taean."),
                      ("Doyun", "The beach candidates are Gangneung and Taean.")],
              "Does Doyun's reply in the last line repeat what was already said, speak other people's lines, "
              "or have nothing to do with the flow?", 0.8)),
    ]


def cmd_probe(a) -> int:
    client = LLMClient(a.url, model=a.model, api_key=a.api_key, thinking_off=not a.thinking_on,
                       timeout=a.timeout)
    log = os.path.join(ROOT, "logs", "decisions_probe.jsonl") if a.log else None
    decider = Decider(client, rotations=a.rotations if a.rotations in ("adaptive", "full") else int(a.rotations),
                      log_path=log)
    if a.backend != "llm":
        decider = make_decider(a.backend, decider, julia_url=a.julia_url, timeout=min(a.timeout, 30.0),
                               trust=a.trust, log_path=log)
    judge = ConversationJudge(decider, roster=ROSTER)
    rows = []
    t_start = time.time()
    for name, expected, fn in (probe_cases_en() if a.lang == "en" else probe_cases()):
        try:
            v = fn(judge)
        except LLMError as e:
            print(f"[ERROR] {name}: {e}")
            return 2
        d = v.decision
        ok = d.answer == expected
        rows.append((name, expected, d, ok, v.value))
        conf = "-" if d.confidence is None else f"{d.confidence:.2f}"
        print(f"{'OK  ' if ok else 'MISS'} {name:34s} -> {str(d.answer)[:24]:24s} p={conf:5s} {d.level:6s} "
              f"mass={d.label_mass:.2f} calls={d.calls} {d.ms:7.0f} ms")
    total = time.time() - t_start
    n_ok = sum(1 for r in rows if r[3])
    levels = sorted({r[2].level for r in rows})
    ms = [r[2].ms for r in rows]
    masses = [r[2].label_mass for r in rows if r[2].level in ("L0", "raw")]
    by_level = {lv: sum(1 for r in rows if r[2].level == lv) for lv in levels}
    acted = sum(1 for r in rows if r[4] is not None)
    acted_ok = sum(1 for r in rows if r[4] is not None and r[3])
    backend = a.backend if a.backend == "llm" else f"{a.backend} ({a.julia_url}, trust {a.trust})"
    summary = [
        f"backend: {backend}   lang: {a.lang}   server: {a.url}   thinking_off: {not a.thinking_on}   "
        f"rotations: {a.rotations}",
        f"accuracy: {n_ok}/{len(rows)}   levels: {', '.join(f'{k} x{v}' for k, v in by_level.items())}",
        f"acted above threshold: {acted}/{len(rows)} (right when acted: {acted_ok}/{acted})",
        f"decision ms: median {statistics.median(ms):.0f}, max {max(ms):.0f}   total {total:.1f} s",
        f"label mass: min {min(masses):.2f}, median {statistics.median(masses):.2f}" if masses else
        "label mass: n/a (no logprobs from the server)",
    ]
    print("\n".join("RESULT " + s for s in summary))
    if a.report:
        os.makedirs(os.path.dirname(a.report), exist_ok=True)
        with open(a.report, "w", encoding="utf-8") as f:
            f.write("# chatup probe\n\n")
            f.write(f"- time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            for s in summary:
                f.write(f"- {s}\n")
            f.write("\n| case | expected | answer | p | level | label mass | calls | ms | ok |\n")
            f.write("|---|---|---|---|---|---|---|---|---|\n")
            for name, expected, d, ok, _ in rows:
                conf = "-" if d.confidence is None else f"{d.confidence:.2f}"
                f.write(f"| {name} | {expected} | {d.answer} | {conf} | {d.level} | {d.label_mass:.2f} | "
                        f"{d.calls} | {d.ms:.0f} | {'OK' if ok else 'MISS'} |\n")
            f.write("\n## distributions\n\n")
            for name, _, d, _, _ in rows:
                f.write(f"- {name}: " + json.dumps(d.distribution, ensure_ascii=False) + "\n")
        print(f"Saved: {a.report}")
    return 0


def _load_personas(path: str):
    from chatup.loop import Persona
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    return [Persona(p["name"], p["system"], p.get("voice", "")) for p in data["personas"]], data.get("roster", "")


def cmd_chat(a) -> int:
    from chatup.loop import ConversationLoop, Hooks, LoopConfig

    client = LLMClient(a.url, model=a.model, api_key=a.api_key, thinking_off=not a.thinking_on)
    personas, roster = _load_personas(a.personas)
    judge = None
    if not a.no_judge:
        log = os.path.join(ROOT, "logs", "decisions_chat.jsonl")
        judge = ConversationJudge(Decider(client, log_path=log), roster=roster)
    voice = None
    if a.voices:
        from chatup.voice import DotsTtsEngine, SoundDevicePlayer, VoiceBank, VoiceWorker
        voice = VoiceWorker(DotsTtsEngine(language=a.language), VoiceBank(a.voices), SoundDevicePlayer())

    class Print(Hooks):
        def on_clause(self, persona, clause):
            tag = f"[{clause.emotion}]" + ("".join(f"<{g}>" for g in clause.gestures))
            print(f"  {persona} {tag} {clause.text}", flush=True)

        def on_line(self, line):
            if line.note:
                print(f"  ({line.speaker}: {line.note})", flush=True)

        def on_image(self, persona, prompt):
            print(f"  [image request from {persona}] {prompt}", flush=True)

        def on_route(self, action, verdict, lines):
            print(f"  [route] {action} (p={verdict.decision.confidence:.2f})", flush=True)

        def on_decision(self, name, verdict):
            if a.show_decisions:
                d = verdict.decision
                conf = "-" if d.confidence is None else f"{d.confidence:.2f}"
                print(f"    <{name}: {d.answer} p={conf} acted={verdict.value is not None} {d.ms:.0f}ms>",
                      flush=True)

        def on_state(self, state, detail=""):
            print(f"  <{state}: {detail}>", flush=True)

    cfg = LoopConfig(idle_seconds=a.idle, max_auto_turns=a.max_auto)
    loop = ConversationLoop(client, personas, judge=judge, voice=voice, config=cfg, hooks=Print())
    stop = threading.Event()
    th = threading.Thread(target=loop.run, args=(stop,), daemon=True)
    th.start()
    print("Type a line and press Enter. Empty line or /quit ends. The characters talk on their own "
          f"after {a.idle:.0f}s of silence.")
    try:
        for raw in sys.stdin:
            text = raw.strip()
            if not text or text == "/quit":
                break
            loop.user_says(text)
    except KeyboardInterrupt:
        pass
    stop.set()
    if voice is not None:
        voice.close()
    th.join(timeout=5)
    return 0


def cmd_voices(a) -> int:
    from chatup.voice import VoiceBank
    bank = VoiceBank(a.bank)
    personas = a.personas.split(",") if a.personas else sorted(
        d for d in os.listdir(a.bank) if os.path.isdir(os.path.join(a.bank, d)))
    for p in personas:
        print(f"{p}: {', '.join(bank.emotions(p)) or '(none)'}")
    problems = bank.check(personas)
    for pr in problems:
        print("PROBLEM " + pr)
    if a.synth:
        from chatup.shaper import Clause
        from chatup.voice import DotsTtsEngine, VoiceWorker, WavWriter
        writer = WavWriter(a.out)
        worker = VoiceWorker(DotsTtsEngine(language=a.language), bank, writer)
        for p in personas:
            for e in bank.emotions(p):
                worker.say(0, p, Clause(a.synth, emotion=e))
        worker.wait_idle()
        worker.close()
        print(f"Saved samples in {a.out}")
    return 1 if problems and a.strict else 0


def cmd_report(a) -> int:
    from chatup.bridge import summarize
    text = summarize(a.log)
    print(text)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {a.out}")
    return 0


def main(argv=None) -> int:
    _utf8_console()
    ap = argparse.ArgumentParser(prog="python -m chatup")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def server_args(p):
        p.add_argument("--url", default="http://127.0.0.1:5678", help="the chatbot's LLM server")
        p.add_argument("--model", default=None)
        p.add_argument("--api-key", default=None)
        p.add_argument("--thinking-on", action="store_true", help="do not send enable_thinking=false")

    p = sub.add_parser("probe")
    server_args(p)
    p.add_argument("--rotations", default="adaptive", help="adaptive | full | N")
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--report", default=None, help="write a markdown report here")
    p.add_argument("--log", action="store_true", help="append decisions to logs/decisions_probe.jsonl")
    p.add_argument("--backend", default="llm", choices=("llm", "julia", "cascade"),
                   help="llm: the LLM at --url; julia: Julia-1 at --julia-url; cascade: julia, llm when unsure")
    p.add_argument("--julia-url", default=JULIA_URL, help="tools/julia_router.py --serve")
    p.add_argument("--trust", type=float, default=0.9, help="cascade: julia answers alone at or above this p")
    p.add_argument("--lang", default="ko", choices=("ko", "en"), help="en: the same cases in English")
    p.set_defaults(fn=cmd_probe)

    p = sub.add_parser("chat")
    server_args(p)
    p.add_argument("--personas", default=os.path.join(ROOT, "examples", "personas.json"))
    p.add_argument("--no-judge", action="store_true", help="rules only, for comparison")
    p.add_argument("--show-decisions", action="store_true")
    p.add_argument("--idle", type=float, default=8.0)
    p.add_argument("--max-auto", type=int, default=8)
    p.add_argument("--voices", default=None, help="voice bank folder (needs dots.tts and sounddevice)")
    p.add_argument("--language", default="ko")
    p.set_defaults(fn=cmd_chat)

    p = sub.add_parser("voices")
    p.add_argument("--bank", required=True)
    p.add_argument("--personas", default="")
    p.add_argument("--synth", default="", help="render this sentence once per emotion (needs dots.tts)")
    p.add_argument("--out", default=os.path.join(ROOT, "out", "voices"))
    p.add_argument("--language", default="ko")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(fn=cmd_voices)

    p = sub.add_parser("report")
    p.add_argument("--log", required=True, help="hooks.jsonl written by JudgeBridge")
    p.add_argument("--out", default=None)
    p.set_defaults(fn=cmd_report)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
