import math
import os
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatup.llm import Cancelled, CancelToken, LLMClient, LLMError, StallError  # noqa: E402
from mockserver import MockLLM  # noqa: E402


@pytest.fixture
def mock():
    m = MockLLM().start()
    yield m
    m.stop()


def test_stream_yields_pieces_and_sends_thinking_off(mock):
    c = LLMClient(mock.url + "/v1")
    out = list(c.stream_chat([{"role": "user", "content": "hi"}], max_tokens=10))
    assert out == ["안녕", "하세요.", " 반가워요."]
    body = mock.requests[-1]
    assert body["stream"] is True
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["max_tokens"] == 10


def test_thinking_on_sends_no_template_kwargs(mock):
    c = LLMClient(mock.url, thinking_off=False, slot_id=1)
    list(c.stream_chat([{"role": "user", "content": "hi"}]))
    assert "chat_template_kwargs" not in mock.requests[-1]
    assert mock.requests[-1]["id_slot"] == 1


def test_cancel_unblocks_a_slow_stream(mock):
    mock.reply_pieces = ["a"] * 50
    mock.piece_delay = 0.2
    c = LLMClient(mock.url)
    tok = CancelToken()
    got = []
    t0 = time.monotonic()
    threading.Timer(0.3, tok.cancel).start()
    with pytest.raises(Cancelled):
        for p in c.stream_chat([{"role": "user", "content": "x"}], cancel=tok):
            got.append(p)
    assert time.monotonic() - t0 < 2.0
    assert 0 < len(got) < 50


def test_stall_timeout(mock):
    mock.first_delay = 1.5
    c = LLMClient(mock.url)
    with pytest.raises(StallError):
        list(c.stream_chat([{"role": "user", "content": "x"}], stall_timeout=0.3))


def test_first_token_logprobs(mock):
    mock.logprobs = lambda body: [("B", math.log(0.7)), ("A", math.log(0.2)), (" C", math.log(0.05))]
    c = LLMClient(mock.url)
    ft = c.first_token_logprobs([{"role": "user", "content": "q"}], top_n=5)
    assert ft.has_logprobs
    assert ft.top[0][0] == "B"
    body = mock.requests[-1]
    assert body["logprobs"] is True and body["top_logprobs"] == 5
    assert body["max_tokens"] == 1 and body["temperature"] == 0.0


def test_first_token_without_logprobs(mock):
    mock.reply_pieces = ["A"]
    c = LLMClient(mock.url)
    ft = c.first_token_logprobs([{"role": "user", "content": "q"}])
    assert not ft.has_logprobs and ft.text == "A"


def test_http_error_is_llm_error(mock):
    mock.status = 500
    c = LLMClient(mock.url)
    with pytest.raises(LLMError, match="HTTP 500"):
        c.chat([{"role": "user", "content": "q"}])


def test_unreachable_server():
    c = LLMClient("http://127.0.0.1:9", timeout=1)
    with pytest.raises(LLMError):
        c.chat([{"role": "user", "content": "q"}])
