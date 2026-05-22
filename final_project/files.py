import os
import re

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

_FILE_PATTERN = re.compile(r'@::(.+?)::')


def expand_file_refs(text: str) -> str:
    """Replace @::filepath:: markers with file contents."""

    def replace_match(match: re.Match[str]) -> str:
        path = match.group(1)
        content = _read_file_safe(path)
        return content if content is not None else match.group(0)

    return _FILE_PATTERN.sub(replace_match, text)


def has_file_refs(text: str) -> bool:
    return bool(_FILE_PATTERN.search(text))


def _read_file_safe(path: str) -> str | None:
    try:
        size = os.path.getsize(path)
        if size > MAX_FILE_SIZE:
            print(f'Предупреждение: файл {path} превышает 5 МБ, пропускаю.')
            return None
        with open(path, encoding='utf-8', errors='replace') as f:
            return f.read()
    except FileNotFoundError:
        print(f'Предупреждение: файл не найден: {path}')
        return None
    except OSError as exc:
        print(f'Предупреждение: не удалось прочитать {path}: {exc}')
        return None


def chunk_by_paragraphs(text: str, paragraph_count: int = 1) -> list[str]:
    """Split text into chunks of paragraph_count lines each."""
    lines = [line for line in text.split('\n') if line.strip()]
    chunks = []
    for i in range(0, len(lines), paragraph_count):
        chunk = '\n'.join(lines[i : i + paragraph_count])
        if chunk:
            chunks.append(chunk)
    return chunks


def chunk_by_length(text: str, length: int) -> list[str]:
    """Split text into chunks of at most length characters."""
    return [text[i : i + length] for i in range(0, len(text), length)]


def parse_file_chunk_args(command: str) -> tuple[int | None, int | None, bool]:
    """Parse /file_chunk command options.

    Returns:
        (paragraph_count, char_length, auto_mode)
    """
    auto_mode = '-y' in command

    para_match = re.search(r'paragraph=(\d+)', command)
    paragraph_count = int(para_match.group(1)) if para_match else None

    len_match = re.search(r'len=(\d+)', command)
    char_length = int(len_match.group(1)) if len_match else None

    return paragraph_count, char_length, auto_mode
