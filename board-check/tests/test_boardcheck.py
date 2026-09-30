import csv
import json
import math
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "chat-upgrade", "tests"))

import boardcheck as bc  # noqa: E402
from mockserver import MockLLM  # noqa: E402

PIL = pytest.importorskip("PIL.Image")


def make_board(root):
    root.mkdir()
    panels = []
    for n, (shot, cast, action) in enumerate([("close-up", ["하나"], "웃는다"),
                                                ("wide shot", ["하나", "도윤"], "걷는다"),
                                                ("medium", [], "")], start=1):
        PIL.new("RGB", (640, 360), (40 * n, 80, 120)).save(root / f"p{n:02d}.png")
        panels.append({"panel_no": n, "shot": shot, "characters": cast, "action": action,
                       "lines": [{"speaker": "하나", "text": "안녕"}] if n == 1 else []})
    (root / "manifest.json").write_text(json.dumps({"title": "t", "panels": panels}, ensure_ascii=False),
                                        encoding="utf-8")
    return root


def text_of(body):
    c = body["messages"][-1]["content"]
    return c[-1]["text"] if isinstance(c, list) else c


def oracle(body):
    t = text_of(body)
    if re.search(r"Answer (Yes|No) or (Yes|No)\.", t):
        bad_hands = "손" in t.split("Question:")[1] and "걷는다" in t
        p = 0.1 if bad_hands else 0.95
        return [("Yes", math.log(p)), ("No", math.log(1 - p))]
    opts = re.findall(r"^([A-Z])\. (.*)$", t, re.M)
    cast = re.search(r"등장인물: (.*)", t)
    n = len(cast.group(1).split(", ")) if cast else 0
    want = "클로즈업" if "샷 크기" in t else f"{n}명"
    top = [(lab, math.log(0.85 if o.strip() == want else 0.15 / (len(opts) - 1))) for lab, o in opts]
    return sorted(top, key=lambda x: x[1], reverse=True)


@pytest.fixture
def mock():
    m = MockLLM().start()
    m.logprobs = oracle
    yield m
    m.stop()


def test_helpers():
    assert bc.shot_index("Extreme close-up of eyes") == 0
    assert bc.shot_index("CU") == 1 and bc.shot_index("클로즈업") == 1
    assert bc.shot_index("MS, eye level") == 2 and bc.shot_index("wide shot") == 4
    assert bc.shot_index("over the shoulder") is None
    assert bc.as_names([{"name": "하나"}, "도윤"]) == ["하나", "도윤"]
    assert bc.as_names("하나, 도윤") == ["하나", "도윤"]


def test_map_guesses_keys(tmp_path, capsys):
    board = make_board(tmp_path / "b")
    assert bc.main(["map", str(board / "manifest.json")]) == 0
    m = json.loads((board / "board_map.json").read_text(encoding="utf-8"))
    assert m["shot"] == "shot" and m["cast"] == "characters" and m["action"] == "action" and m["lines"] == "lines"
    out = capsys.readouterr().out
    assert "shot: str" in out and "웃는다" not in out            # keys and types only, no values


def test_run_logprobs_and_feedback(tmp_path, mock, capsys):
    board = make_board(tmp_path / "b")
    out = tmp_path / "out"
    assert bc.main(["run", "--board", str(board), "--out", str(out), "--url", mock.url, "--continuity",
                    "--checks", "full"]) == 0
    r = json.loads((out / "review.json").read_text(encoding="utf-8"))
    p1, p2, p3 = (r["panels"][f"p{n:02d}"] for n in (1, 2, 3))
    assert p1["status"] == "ok" and p1["checks"]["shot_size"]["p_bad"] < 0.2
    assert p2["status"] == "bad" and p2["checks"]["hands_ok"]["p_bad"] > 0.8
    assert p2["checks"]["shot_size"]["p_bad"] > 0.5 and "looks 클로즈업" in p2["checks"]["shot_size"]["note"]
    assert "continuity" in p2["checks"] and "continuity" not in p1["checks"]
    assert "people_count" not in p3["checks"] and "action_ok" not in p3["checks"]
    html = (out / "review.html").read_text(encoding="utf-8")
    assert html.index('data-id="p02"') < html.index('data-id="p01"')      # problems first
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert "하나" not in summary and "웃는다" not in summary and "손 (hands_ok)" in summary
    calls = len(mock.requests)
    assert bc.main(["run", "--board", str(board), "--out", str(out), "--url", mock.url]) == 0
    assert len(mock.requests) == calls                                      # resumes, nothing re-asked

    fb = tmp_path / "feedback.csv"
    with open(fb, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["panel", "status", "human", "disputed"])
        w.writerow(["p02", "bad", "redo", "shot_size"])
        w.writerow(["p01", "ok", "redo", ""])
        w.writerow(["p03", "ok", "ok", ""])
    assert bc.main(["feedback", "--review", str(out), "--csv", str(fb), "--out", str(tmp_path / "FB.md")]) == 0
    text = (tmp_path / "FB.md").read_text(encoding="utf-8")
    assert "| 손 (hands_ok) | 1 | 1 | 0 | 100% |" in text
    assert "| 샷 크기 (shot_size) | 1 | 0 | 1 | 0% |" in text
    assert "that the model passed: 1" in text


def test_decision_backend(tmp_path):
    seen = []

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
            seen.append((self.path, body))
            props = body["schema"]["properties"]
            fields = {}
            for k, v in props.items():
                if v["type"] == "boolean":
                    fields[k] = {"value": k != "hands_ok", "probability": 0.9}
                else:
                    fields[k] = {"value": v["choices"][1], "probability": 0.8}
            data = json.dumps({"object": "decision", "results": [{"fields": fields}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        board = make_board(tmp_path / "b")
        out = tmp_path / "out"
        url = f"http://127.0.0.1:{srv.server_address[1]}/v1"
        assert bc.main(["run", "--board", str(board), "--out", str(out), "--url", url, "--backend", "decision",
                        "--ids", "p01", "--checks", "full"]) == 0
        path, body = seen[0]
        assert path == "/decision" and len(seen) == 1                       # every question in one call
        assert set(body) >= {"instructions", "schema", "contexts", "images"}
        assert len(body["contexts"]) == 1 and len(body["images"][0]) == 1
        r = json.loads((out / "review.json").read_text(encoding="utf-8"))["panels"]["p01"]
        assert r["checks"]["hands_ok"]["p_bad"] == pytest.approx(0.9)
        assert r["checks"]["face_ok"]["p_bad"] == pytest.approx(0.1)
        assert r["checks"]["shot_size"]["p_bad"] < 0.3                      # 클로즈업 chosen, expected close-up
    finally:
        srv.shutdown()


def test_identity_rules():
    class F:
        def __init__(self, h):
            self.height = h
    ok = [(F(80), "A", 0.6, None)]
    assert bc.identity_verdict(ok, ["A"])[0] == 1.0
    assert bc.identity_verdict([(F(80), "B", 0.6, None)], ["A"])[0] < 0.2
    assert bc.identity_verdict([(F(80), None, 0.1, None)], ["A"])[0] < 0.5
    assert bc.identity_verdict([(F(10), "B", 0.6, None)], ["A"])[0] == 1.0     # too small to judge


def test_core_checks_in_parallel(tmp_path, mock):
    board = make_board(tmp_path / "b")
    out = tmp_path / "out"
    assert bc.main(["run", "--board", str(board), "--out", str(out), "--url", mock.url, "--workers", "3"]) == 0
    r = json.loads((out / "review.json").read_text(encoding="utf-8"))["panels"]
    assert len(r) == 3
    for p in r.values():
        assert set(p["checks"]) <= bc.CORE
    assert {"hands_ok", "face_ok", "no_text", "matches_spec"} <= set(r["p01"]["checks"])
    assert "shot_size" not in r["p01"]["checks"] and "body_ok" not in r["p01"]["checks"]
    # one reading per question by default: 5 core questions, no second order
    assert len(mock.requests) == 5 + 5 + 4          # p01: 4 yes/no + count, p02: same, p03: 4 yes/no


def test_one_catches_a_squeezed_picture(tmp_path, mock, capsys):
    tall = tmp_path / "tall.png"
    PIL.new("RGB", (480, 640), (60, 60, 60)).save(tall)
    out = tmp_path / "one.json"
    rc = bc.main(["one", "--image", str(tall), "--action", "앉아서 조종간을 잡는다", "--location", "조종석",
                  "--cast", "김철", "--aspect", "16:9", "--url", mock.url, "--out", str(out)])
    assert rc == 1
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["status"] == "bad" and r["checks"]["aspect_ok"]["p_bad"] == 1.0
    assert "got 480x640" in r["checks"]["aspect_ok"]["note"]
    assert {"matches_spec", "action_ok", "place_ok", "people_count"} <= set(r["checks"])
    assert "RESULT bad" in capsys.readouterr().out


def test_one_passes_a_matching_picture(tmp_path, mock):
    wide = tmp_path / "wide.png"
    PIL.new("RGB", (1536, 864), (60, 60, 60)).save(wide)
    assert bc.main(["one", "--image", str(wide), "--action", "앉아서 조종간을 잡는다", "--cast", "김철",
                    "--aspect", "16:9", "--url", mock.url]) == 0


def test_one_never_passes_silently(tmp_path, capsys):
    wide = tmp_path / "wide.png"
    PIL.new("RGB", (1536, 864), (60, 60, 60)).save(wide)
    rc = bc.main(["one", "--image", str(wide), "--action", "앉는다", "--url", "http://127.0.0.1:9", "--timeout", "2"])
    assert rc == 2 and "the model was not asked" in capsys.readouterr().out
    assert bc.main(["one", "--image", str(tmp_path / "missing.png")]) == 2
