import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "chat-upgrade"))

import h3compose as hc  # noqa: E402
import h3lint  # noqa: E402

FRAMES = 5 + 17 * 7            # 124 frames, 5.17 s

SECTIONS = {
    "scene": "Night on a rain-polished rooftop; <Subject 1> in a white dobok stands by the railing.",
    "beats": [{"start": 0.0, "end": 2.0, "action": "<Subject 1> breathes slowly and looks at the city"},
              {"start": 2.0, "end": 5.17, "action": "<Subject 1> tightens the black belt and lifts the chin"}],
    "acting": "Steady breath, calm eyes, weight centred on both feet.",
    "camera": "One slow push-in at chest height.",
    "light": "Cool blue city glow from the left, warm rim light from a sign behind.",
    "sound": "Rain on concrete, distant traffic.",
    "music": "",
    "dialogue": [{"subject": 1, "lang": "Korean", "text": "간다.", "start": 2.5}],
}
SUBJ = [{"look": "a young pilot with short black hair", "gender": "male", "picture": 1}]


def shot(mode="base", **kw):
    d = {"mode": mode, "frames": FRAMES, "subjects": SUBJ, "sections": dict(SECTIONS), "final_chunk": True}
    d.update(kw)
    return d


def clean(prompt, **kw):
    return {k for k in h3lint.check(prompt, **kw) if not k.startswith("_")}


def test_compose_all_modes_pass_lint():
    dur = FRAMES / 24
    for mode in ("base", "i2v", "ref"):
        p = hc.compose(shot(mode))
        assert clean(p, duration=dur, pictures=1) == set(), (mode, h3lint.check(p, duration=dur))
    lip = hc.compose(shot("ref", lipsync_audio=True))
    assert clean(lip, duration=dur) == set()
    assert "fully_copy" in lip and "[reference generation + audio reuse]" in lip
    assert "2.00s-end:" in hc.compose(shot()) and "<Subject 1> (S1): <d>[Korean] 간다.</d>" in hc.compose(shot())
    assert hc.compose(shot("i2v")).startswith("For the target video")


def test_validate_clip_rules():
    assert "frames_grid" in hc.validate(shot(frames=120))
    late = dict(SECTIONS, dialogue=[{"subject": 1, "text": "간다", "start": 4.6}])
    assert "dialogue_at_chunk_end" in hc.validate(shot(sections=late, final_chunk=False))
    assert "dialogue_at_chunk_end" not in hc.validate(shot(sections=late, final_chunk=True))
    early = dict(SECTIONS, dialogue=[{"subject": 1, "text": "간다", "start": 0.3}])
    assert "dialogue_at_chunk_start" in hc.validate(shot(sections=early, continues_previous=True))
    ghost = dict(SECTIONS, dialogue=[{"subject": 2, "text": "누구", "start": 1.0}])
    assert "dialogue_subject" in hc.validate(shot(sections=ghost))
    assert "no_reference" in hc.validate(shot("ref", subjects=[{"look": "x", "gender": "f"}]))


class FakeLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def chat(self, messages, max_tokens=900, temperature=0.4):
        self.calls.append(messages)
        return self.replies.pop(0)


def content(**over):
    d = {k: SECTIONS[k] for k in ("scene", "beats", "acting", "camera", "light", "sound", "music")}
    d.update(over)
    return json.dumps(d, ensure_ascii=False)


def test_writer_retries_with_reasons():
    bad = content(acting="She breathes; his gaze stays still. Do not blink.")
    llm = FakeLLM(["<think>x</think> here: " + bad, content()])
    res = hc.write(shot(), {"beat": "pilot resolve"}, llm)
    assert res["tries"] == 2 and res["problems"] == {} and res["prompt"]
    feedback = llm.calls[1][-1]["content"]
    assert "pronoun_mix" in feedback and "negative_language" in feedback
    first_user = json.loads(llm.calls[0][1]["content"])
    assert first_user["subjects"][0]["tag"] == "<Subject 1>" and first_user["spoken_lines"][0]["text"] == "간다."


def test_writer_split_and_bad_json_and_precheck():
    res = hc.write(shot(), {}, FakeLLM([json.dumps({"split": ["pilot close-up", "robot head wide reveal"]})]))
    assert res["split"] == ["pilot close-up", "robot head wide reveal"] and res["prompt"] is None
    res = hc.write(shot(), {}, FakeLLM(["not json", "still not", "nope"]))
    assert res["prompt"] is None and "not_json" in res["problems"] and res["tries"] == 3
    res = hc.write(shot(frames=100), {}, FakeLLM([]))
    assert res["tries"] == 0 and "frames_grid" in res["problems"]
    beats_bad = content(beats=[{"start": 1.0, "end": 9.0, "action": "x"}])
    res = hc.write(shot(), {}, FakeLLM([beats_bad] * 3))
    assert "beats_outside" in res["problems"] and "beats_start" in res["problems"]


class FakeDecision:
    def __init__(self, yes):
        self.yes, self.confidence = yes, yes


class FakeDecider:
    def __init__(self, flags):
        self.flags = list(flags)

    def decide(self, state, q):
        return FakeDecision(self.flags.pop(0))


def test_writer_semantic_check():
    dec = FakeDecider([0.93, 0.1, 0.05, 0.1])            # first try: two compositions; second: clean
    res = hc.write(shot(), {}, FakeLLM([content(), content()]), decider=dec)
    assert res["tries"] == 2 and res["problems"] == {}
    assert hc.semantic_check("x", FakeDecider([0.5, 0.95])) == {"camera_mismatch": "p=0.95"}
