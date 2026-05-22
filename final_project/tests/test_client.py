from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import openai
import pytest

from client import LLMClient, LLMError
from config import Config


def _make_config(**kwargs: object) -> Config:
    defaults: dict[str, object] = {
        'api_key': 'test-key',
        'api_host': 'http://localhost:11434/v1/',
        'model': 'gemma3',
        'limit_message': None,
        'limit_chars': None,
        'temperature': 0.7,
        'system_prompt': None,
    }
    defaults.update(kwargs)
    return Config(**defaults)  # type: ignore[arg-type]


def test_llm_error_is_exception() -> None:
    err = LLMError('something went wrong')
    assert isinstance(err, Exception)
    assert str(err) == 'something went wrong'


def test_llm_client_init() -> None:
    cfg = _make_config()
    with patch('client.openai.OpenAI') as mock_openai:
        client = LLMClient(cfg)
        mock_openai.assert_called_once_with(api_key='test-key', base_url='http://localhost:11434/v1/')
        assert client._temperature == 0.7


def _make_chunk(content: str | None) -> MagicMock:
    chunk = MagicMock()
    chunk.choices[0].delta.content = content
    return chunk


def test_send_stream_yields_content() -> None:
    cfg = _make_config()

    chunks = [_make_chunk('Hello'), _make_chunk(' world'), _make_chunk(None)]

    with patch('client.openai.OpenAI') as mock_openai:
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.__iter__ = MagicMock(return_value=iter(chunks))

        client = LLMClient(cfg)
        result = list(client.send_stream([{'role': 'user', 'content': 'hi'}], 'gemma3'))

    assert result == ['Hello', ' world']


def test_send_stream_raises_llmerror_on_connection_error() -> None:
    cfg = _make_config()

    with patch('client.openai.OpenAI') as mock_openai:
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.side_effect = openai.APIConnectionError(request=MagicMock())

        client = LLMClient(cfg)
        gen: Iterator[str] = client.send_stream([{'role': 'user', 'content': 'hi'}], 'gemma3')

        with pytest.raises(LLMError, match='Ошибка подключения'):
            next(gen)


def test_send_stream_raises_llmerror_on_status_error() -> None:
    cfg = _make_config()

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.headers = {}

    with patch('client.openai.OpenAI') as mock_openai:
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.side_effect = openai.AuthenticationError(
            message='Unauthorized', response=mock_response, body=None
        )

        client = LLMClient(cfg)
        gen: Iterator[str] = client.send_stream([{'role': 'user', 'content': 'hi'}], 'gemma3')

        with pytest.raises(LLMError):
            next(gen)
