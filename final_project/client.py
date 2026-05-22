from collections.abc import Iterator
from typing import cast

import openai
from openai import Stream
from openai.types.chat import ChatCompletionChunk

from config import Config


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, config: Config) -> None:
        self._client = openai.OpenAI(
            api_key=config.api_key,
            base_url=config.api_host,
        )
        self._temperature = config.temperature

    def send_stream(
        self,
        messages: list[dict[str, str]],
        model: str,
    ) -> Iterator[str]:
        try:
            stream = cast(
                Stream[ChatCompletionChunk],
                self._client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore[arg-type]
                    temperature=self._temperature,
                    stream=True,
                ),
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except openai.APIConnectionError as exc:
            raise LLMError(f'Ошибка подключения: {exc}') from exc
        except openai.APIStatusError as exc:
            raise LLMError(f'Ошибка API {exc.status_code}: {exc.message}') from exc
        except openai.OpenAIError as exc:
            raise LLMError(f'Ошибка: {exc}') from exc
