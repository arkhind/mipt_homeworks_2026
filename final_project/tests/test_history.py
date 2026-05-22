import pytest

from history import Message, MessageHistory


def test_add_single_message() -> None:
    h = MessageHistory()
    h.add(Message(role='user', content='hello'))
    assert len(h) == 1
    assert h.to_list() == [{'role': 'user', 'content': 'hello'}]


def test_add_multiple_messages() -> None:
    h = MessageHistory()
    h.add(Message(role='user', content='hi'))
    h.add(Message(role='assistant', content='hello'))
    assert len(h) == 2


def test_to_list_format() -> None:
    h = MessageHistory()
    h.add(Message(role='user', content='test'))
    result = h.to_list()
    assert result == [{'role': 'user', 'content': 'test'}]


def test_trim_by_message_count() -> None:
    h = MessageHistory(limit_message=3)
    for i in range(5):
        h.add(Message(role='user', content=f'msg{i}'))
    assert len(h) == 3
    assert h.to_list()[0]['content'] == 'msg2'


def test_trim_by_message_count_exact() -> None:
    h = MessageHistory(limit_message=2)
    h.add(Message(role='user', content='a'))
    h.add(Message(role='user', content='b'))
    assert len(h) == 2
    h.add(Message(role='user', content='c'))
    assert len(h) == 2
    assert h.to_list()[0]['content'] == 'b'
    assert h.to_list()[1]['content'] == 'c'


def test_trim_by_chars_removes_oldest() -> None:
    h = MessageHistory(limit_chars=10)
    h.add(Message(role='user', content='hello'))
    h.add(Message(role='user', content='world'))
    assert len(h) == 2
    h.add(Message(role='user', content='added'))
    assert len(h) == 2


def test_trim_by_chars_removes_enough() -> None:
    h = MessageHistory(limit_chars=6)
    h.add(Message(role='user', content='12345'))
    h.add(Message(role='user', content='67890'))
    assert len(h) == 1
    assert h.to_list()[0]['content'] == '67890'


def test_trim_single_message_overflow() -> None:
    h = MessageHistory(limit_chars=3)
    h.add(Message(role='user', content='hello'))
    assert len(h) == 1
    assert h.to_list()[0]['content'] == 'llo'


def test_clear() -> None:
    h = MessageHistory()
    h.add(Message(role='user', content='hello'))
    h.add(Message(role='assistant', content='hi'))
    h.clear()
    assert len(h) == 0
    assert h.to_list() == []


def test_both_limits() -> None:
    h = MessageHistory(limit_message=5, limit_chars=20)
    for i in range(10):
        h.add(Message(role='user', content=f'msg{i}'))
    assert len(h) <= 5
    total = sum(len(m['content']) for m in h.to_list())
    assert total <= 20


def test_no_limits() -> None:
    h = MessageHistory()
    for _ in range(100):
        h.add(Message(role='user', content='x'))
    assert len(h) == 100


def test_trim_chars_single_message_exact() -> None:
    h = MessageHistory(limit_chars=5)
    h.add(Message(role='user', content='hello'))
    assert h.to_list()[0]['content'] == 'hello'


@pytest.mark.parametrize('limit', [1, 2, 10])
def test_message_limit_never_exceeded(limit: int) -> None:
    h = MessageHistory(limit_message=limit)
    for i in range(limit + 5):
        h.add(Message(role='user', content=str(i)))
    assert len(h) <= limit
