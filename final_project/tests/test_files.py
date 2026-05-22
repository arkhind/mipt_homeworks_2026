import pytest

from files import (
    chunk_by_length,
    chunk_by_paragraphs,
    expand_file_refs,
    has_file_refs,
    parse_file_chunk_args,
)


def test_expand_no_refs() -> None:
    assert expand_file_refs('hello world') == 'hello world'


def test_has_file_refs_positive() -> None:
    assert has_file_refs('@::/path/to/file::') is True


def test_has_file_refs_negative() -> None:
    assert has_file_refs('just text') is False


def test_expand_file_ref_basic(tmp_path: pytest.TempPathFactory) -> None:
    f = tmp_path / 'test.txt'  # type: ignore[operator]
    f.write_text('file content')
    result = expand_file_refs(f'Hello @::{f}::')
    assert result == 'Hello file content'


def test_expand_file_not_found(capsys: pytest.CaptureFixture[str]) -> None:
    text = '@::/nonexistent/path/file.txt::'
    result = expand_file_refs(text)
    assert result == text
    captured = capsys.readouterr()
    assert 'Предупреждение' in captured.out


def test_expand_file_too_large(
    tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    f = tmp_path / 'big.txt'  # type: ignore[operator]
    f.write_text('x')
    monkeypatch.setattr('files.MAX_FILE_SIZE', 0)
    result = expand_file_refs(f'@::{f}::')
    assert result == f'@::{f}::'


def test_expand_multiple_refs(tmp_path: pytest.TempPathFactory) -> None:
    f1 = tmp_path / 'a.txt'  # type: ignore[operator]
    f2 = tmp_path / 'b.txt'  # type: ignore[operator]
    f1.write_text('AAA')
    f2.write_text('BBB')
    result = expand_file_refs(f'@::{f1}:: and @::{f2}::')
    assert result == 'AAA and BBB'


def test_chunk_by_paragraphs_single() -> None:
    text = 'line1\nline2\nline3'
    assert chunk_by_paragraphs(text, 1) == ['line1', 'line2', 'line3']


def test_chunk_by_paragraphs_multiple() -> None:
    text = 'a\nb\nc\nd'
    assert chunk_by_paragraphs(text, 2) == ['a\nb', 'c\nd']


def test_chunk_by_paragraphs_skips_empty() -> None:
    text = 'a\n\nb\n\nc'
    assert chunk_by_paragraphs(text, 1) == ['a', 'b', 'c']


def test_chunk_by_paragraphs_odd_count() -> None:
    text = 'a\nb\nc'
    chunks = chunk_by_paragraphs(text, 2)
    assert chunks == ['a\nb', 'c']


def test_chunk_by_length_basic() -> None:
    assert chunk_by_length('abcdefgh', 3) == ['abc', 'def', 'gh']


def test_chunk_by_length_exact() -> None:
    assert chunk_by_length('abcdef', 3) == ['abc', 'def']


def test_chunk_by_length_single() -> None:
    assert chunk_by_length('abc', 10) == ['abc']


def test_parse_args_default() -> None:
    para, length, auto = parse_file_chunk_args('/file_chunk')
    assert para is None
    assert length is None
    assert auto is False


def test_parse_args_paragraph() -> None:
    para, length, auto = parse_file_chunk_args('/filechunk paragraph=5')
    assert para == 5
    assert length is None
    assert auto is False


def test_parse_args_len() -> None:
    para, length, auto = parse_file_chunk_args('/file_chunk len=200')
    assert para is None
    assert length == 200
    assert auto is False


def test_parse_args_auto() -> None:
    para, length, auto = parse_file_chunk_args('/filechunk paragraph=3 -y')
    assert para == 3
    assert auto is True


def test_parse_args_len_auto() -> None:
    _, length, auto = parse_file_chunk_args('/file_chunk len=100 -y')
    assert length == 100
    assert auto is True
