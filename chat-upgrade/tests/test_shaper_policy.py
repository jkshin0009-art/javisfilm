import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatup.policy import TurnPolicy, loop_score, similarity  # noqa: E402
from chatup.shaper import Clause, ReplyShaper  # noqa: E402


def run(chunks, **kw):
    sh = ReplyShaper(**kw)
    ev = []
    for c in chunks:
        ev += sh.feed(c)
    ev += sh.flush()
    return ev, sh


def clauses(ev):
    return [e.clause for e in ev if e.kind == "clause"]


def test_think_and_special_tokens_split_across_chunks():
    ev, _ = run(["<th", "ink>계획: 먼저 인사</thi", "nk>안녕하세요.", " 반가워요<|im_", "end|>"])
    assert [c.text for c in clauses(ev)] == ["안녕하세요.", "반가워요"]


def test_unclosed_think_is_never_spoken():
    ev, _ = run(["<think>끝나지 않는 생각", " 계속"])
    assert clauses(ev) == []


def test_emotion_and_gesture_tags_bind_to_their_clause():
    ev, _ = run(["[hap", "py]좋아요. 날씨가", " 좋네요! [nod]어디 갈까요?", " [[emotion:sad]]아쉽다…"])
    cs = clauses(ev)
    assert [(c.text, c.emotion, c.gestures) for c in cs] == [
        ("좋아요.", "happy", []), ("날씨가 좋네요!", "happy", []),
        ("어디 갈까요?", "happy", ["nod"]), ("아쉽다…", "sad", [])]
    assert cs[2].is_question and not cs[1].is_question


def test_korean_emotion_words_and_unknown_brackets():
    ev, _ = run(["[슬픔]그랬구나. [각주] 표시는 그대로."])
    cs = clauses(ev)
    assert cs[0].emotion == "sad" and cs[0].text == "그랬구나."
    assert cs[1].text == "[각주] 표시는 그대로."


def test_image_tag_becomes_event_in_order():
    ev, _ = run(["[[image: 새벽 바닷가, 두 사람]]이렇게 그려 볼게요. 어때요?"])
    assert ev[0].kind == "image" and ev[0].value == "새벽 바닷가, 두 사람"
    assert [c.text for c in clauses(ev)] == ["이렇게 그려 볼게요.", "어때요?"]


def test_speaker_prefix_removed_and_other_speaker_stops():
    ev, sh = run(["**민지**: 오늘은", " 여기까지 하자.\n준호: 그래 나도"], speaker="민지", others=["준호"])
    assert [c.text for c in clauses(ev)] == ["오늘은 여기까지 하자."]
    assert ev[-1].kind == "stop" and sh.stopped
    assert sh.feed("더 말함") == []


def test_colon_that_is_not_a_name_is_kept():
    ev, _ = run(["주의: 여기 미끄러워요."], speaker="민지", others=["준호"])
    assert clauses(ev)[0].text == "주의: 여기 미끄러워요."


def test_decimals_ellipsis_and_short_merges():
    ev, _ = run(["3.5초 뒤에... 네. 시작합니다. OK. Go on now."])
    assert [c.text for c in clauses(ev)] == ["3.5초 뒤에...", "네. 시작합니다.", "OK. Go on now."]


def test_long_clause_splits_at_comma_then_space():
    long = "이건 정말 길게 이어지는 말인데, " + "쉼표 없이 계속되는 부분이 한참 동안 이어지고 " * 6
    ev, _ = run([long], soft_max=40, hard_max=80)
    cs = clauses(ev)
    assert cs[0].text.endswith(",")
    assert all(len(c.text) <= 80 for c in cs)


def test_first_clause_is_emitted_before_the_reply_ends():
    sh = ReplyShaper()
    assert sh.feed("첫 문장입니다.") == []          # waits for the next character
    ev = sh.feed(" 두 번째")
    assert [e.clause.text for e in ev] == ["첫 문장입니다."]


def test_similarity_and_loop_score():
    assert similarity("오늘 촬영 어땠어?", "오늘 촬영 어땠어?") == 1.0
    assert similarity("오늘 촬영 어땠어?", "바닷가 장소는 정했어") < 0.2
    assert loop_score(["그래 맞아", "응 맞아 맞아", "그래 맞아", "맞아 그래"]) > 0.25
    assert loop_score(["조명은 챙겼어", "대본은 거의 다 됐어", "장소는 강릉으로 하자"]) < 0.1


def test_policy_decisions():
    p = TurnPolicy(max_clauses=3)
    c = lambda t, q=False: Clause(t, is_question=q)
    assert p.check(c("바닷가 장면은 새벽에 찍자."), [], []) == "speak"
    assert p.check(c("넌 어떻게 생각해?", True), [], []) == "speak_last"
    assert p.check(c("바닷가 장면은 새벽에 찍자."), [], ["바닷가 장면은 새벽에 찍자."]) == "drop"
    assert p.check(c("바닷가 장면은 새벽에 찍자."), ["바닷가 장면은 새벽에 찍자."], []) == "stop"
    assert p.check(c("네."), [], ["네."]) == "speak"                   # short lines may repeat
    assert p.check(c("세 번째 문장이다."), ["하나 문장이다", "둘 문장이다"], []) == "speak_last"
    assert p.check(c("네 번째 문장이다."), ["가", "나", "다"], []) == "stop"
    assert TurnPolicy(end_on_question=False).check(c("정말이야?", True), [], []) == "speak"
    assert p.is_repeat_turn("바닷가 장면은 새벽에 찍자.", ["바닷가 장면은 새벽에 찍자!"])
