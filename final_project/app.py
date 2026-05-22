import os

from client import LLMClient, LLMError
from config import Config
from files import chunk_by_length, chunk_by_paragraphs, expand_file_refs, parse_file_chunk_args
from history import Message, MessageHistory

_PROMPT = '>>> '
_DIVIDER = '-' * 60
_QUIT = '\\q'


def _clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


class App:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._history = MessageHistory(
            limit_message=config.limit_message,
            limit_chars=config.limit_chars,
        )
        self._client = LLMClient(config)

    def _build_messages(self) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if self._config.system_prompt:
            messages.append({'role': 'system', 'content': self._config.system_prompt})
        messages.extend(self._history.to_list())
        return messages

    def _stream_response(self, messages: list[dict[str, str]]) -> str:
        full_response = ''
        try:
            for chunk in self._client.send_stream(messages, self._config.model):
                print(chunk, end='', flush=True)
                full_response += chunk
        except KeyboardInterrupt:
            print('\n[Прервано]')
            return full_response
        except LLMError as exc:
            print(f'\nОшибка: {exc}')
            return full_response
        print()
        return full_response

    def _ask(self, user_text: str) -> None:
        self._history.add(Message(role='user', content=user_text))
        response = self._stream_response(self._build_messages())
        if response:
            self._history.add(Message(role='assistant', content=response))

    def _handle_file_chunk(self, command: str) -> None:
        paragraph_count, char_length, auto_mode = parse_file_chunk_args(command)

        print('Введите путь до файла')
        file_path = input(_PROMPT).strip()
        if file_path == _QUIT:
            return

        if not os.path.exists(file_path):
            print(f'Файл не найден: {file_path}')
            return

        try:
            with open(file_path, encoding='utf-8', errors='replace') as f:
                content = f.read()
        except OSError as exc:
            print(f'Не удалось прочитать файл: {exc}')
            return

        print('Принято. Что нужно сделать для каждого фрагмента (User Prompt)?')
        user_prompt = input(_PROMPT).strip()
        if user_prompt == _QUIT:
            return

        print('Принято. Начинаю обработку:')

        if char_length is not None:
            chunks = chunk_by_length(content, char_length)
        elif paragraph_count is not None:
            chunks = chunk_by_paragraphs(content, paragraph_count)
        else:
            chunks = chunk_by_paragraphs(content, 1)

        for i, chunk_text in enumerate(chunks):
            if not auto_mode and i > 0:
                user_input = input(_PROMPT).strip()
                if user_input == _QUIT:
                    break

            temp_messages: list[dict[str, str]] = []
            if self._config.system_prompt:
                temp_messages.append({'role': 'system', 'content': self._config.system_prompt})
            temp_messages.append({'role': 'user', 'content': f'{user_prompt}\n{chunk_text}'})

            self._stream_response(temp_messages)

        print('Обработка файла завершена.')

    def run(self) -> None:
        print('GigaVibeMiptCode — ИИ-ассистент. Введите \\q для выхода.')
        print(_DIVIDER)

        while True:
            try:
                user_input = input(_PROMPT).strip()
            except EOFError:
                print()
                break

            if not user_input:
                continue

            if user_input == _QUIT:
                break

            if user_input == '/reset':
                self._history.clear()
                _clear_screen()
                continue

            if user_input.startswith('/file_chunk') or user_input.startswith('/filechunk'):
                self._handle_file_chunk(user_input)
                continue

            expanded = expand_file_refs(user_input)
            self._ask(expanded)
