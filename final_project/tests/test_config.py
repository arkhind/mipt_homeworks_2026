import pytest

from config import _parse_float, _parse_int, load_config


def test_parse_int_valid() -> None:
    assert _parse_int('42') == 42


def test_parse_int_none() -> None:
    assert _parse_int(None) is None


def test_parse_int_empty() -> None:
    assert _parse_int('') is None


def test_parse_int_invalid() -> None:
    assert _parse_int('abc') is None


def test_parse_int_zero() -> None:
    assert _parse_int('0') is None


def test_parse_int_negative() -> None:
    assert _parse_int('-5') is None


def test_parse_float_valid() -> None:
    assert _parse_float('0.5', 0.7) == 0.5


def test_parse_float_zero() -> None:
    assert _parse_float('0.0', 0.7) == 0.0


def test_parse_float_one() -> None:
    assert _parse_float('1.0', 0.7) == 1.0


def test_parse_float_none() -> None:
    assert _parse_float(None, 0.7) == 0.7


def test_parse_float_out_of_range_high() -> None:
    assert _parse_float('1.5', 0.7) == 0.7


def test_parse_float_out_of_range_low() -> None:
    assert _parse_float('-0.1', 0.7) == 0.7


def test_parse_float_invalid() -> None:
    assert _parse_float('abc', 0.7) == 0.7


def test_load_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('API_KEY', 'test-key')
    monkeypatch.setenv('API_HOST', 'http://localhost:11434/v1/')
    monkeypatch.setenv('LIMIT_MESSAGE', '10')
    monkeypatch.setenv('TEMPERATURE', '0.5')
    monkeypatch.delenv('LIMIT_CHARS', raising=False)
    monkeypatch.delenv('SYSTEM_PROMPT', raising=False)
    monkeypatch.setattr('config._load_yaml', lambda: {})

    cfg = load_config()

    assert cfg.api_key == 'test-key'
    assert cfg.api_host == 'http://localhost:11434/v1/'
    assert cfg.limit_message == 10
    assert cfg.temperature == 0.5
    assert cfg.limit_chars is None


def test_load_config_missing_both_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('API_KEY', raising=False)
    monkeypatch.delenv('API_HOST', raising=False)
    monkeypatch.setattr('config._load_yaml', lambda: {})

    with pytest.raises(SystemExit):
        load_config()


def test_load_config_missing_host_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('API_KEY', 'some-key')
    monkeypatch.delenv('API_HOST', raising=False)
    monkeypatch.setattr('config._load_yaml', lambda: {})

    with pytest.raises(SystemExit):
        load_config()


def test_load_config_env_overrides_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('API_KEY', 'env-key')
    monkeypatch.setenv('API_HOST', 'http://env-host/')
    monkeypatch.delenv('LIMIT_MESSAGE', raising=False)
    monkeypatch.delenv('LIMIT_CHARS', raising=False)
    monkeypatch.delenv('TEMPERATURE', raising=False)
    monkeypatch.delenv('SYSTEM_PROMPT', raising=False)
    monkeypatch.delenv('MODEL', raising=False)
    monkeypatch.setattr('config._load_yaml', lambda: {
        'api_key': 'yaml-key',
        'api_host': 'http://yaml-host/',
        'limit_message': 20,
    })

    cfg = load_config()

    assert cfg.api_key == 'env-key'
    assert cfg.api_host == 'http://env-host/'
    assert cfg.limit_message == 20


def test_load_config_from_yaml(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('API_KEY', raising=False)
    monkeypatch.delenv('API_HOST', raising=False)
    monkeypatch.delenv('LIMIT_MESSAGE', raising=False)
    monkeypatch.delenv('LIMIT_CHARS', raising=False)
    monkeypatch.delenv('TEMPERATURE', raising=False)
    monkeypatch.delenv('SYSTEM_PROMPT', raising=False)
    monkeypatch.delenv('MODEL', raising=False)
    monkeypatch.setattr('config._load_yaml', lambda: {
        'api_key': 'yaml-key',
        'api_host': 'http://localhost/',
        'limit_chars': 2000,
        'system_prompt': 'You are helpful.',
    })

    cfg = load_config()

    assert cfg.api_key == 'yaml-key'
    assert cfg.limit_chars == 2000
    assert cfg.system_prompt == 'You are helpful.'


def test_load_config_default_temperature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('API_KEY', 'k')
    monkeypatch.setenv('API_HOST', 'http://h/')
    monkeypatch.delenv('TEMPERATURE', raising=False)
    monkeypatch.setattr('config._load_yaml', lambda: {})

    cfg = load_config()
    assert cfg.temperature == 0.7
