import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Config:
    api_key: str
    api_host: str
    model: str
    limit_message: int | None
    limit_chars: int | None
    temperature: float
    system_prompt: str | None


def _load_yaml() -> dict[str, Any]:
    path = Path(__file__).parent / 'config.yaml'
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except yaml.YAMLError as exc:
        print(f'Warning: could not parse config.yaml: {exc}')
        return {}
    except OSError as exc:
        print(f'Warning: could not read config.yaml: {exc}')
        return {}


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        result = int(value)
        return result if result > 0 else None
    except ValueError:
        return None


def _parse_float(value: str | None, default: float) -> float:
    if not value:
        return default
    try:
        parsed = float(value)
        return parsed if 0.0 <= parsed <= 1.0 else default
    except ValueError:
        return default


def load_config() -> Config:
    yaml_cfg = _load_yaml()

    api_key = os.environ.get('API_KEY') or str(yaml_cfg.get('api_key', ''))
    api_host = os.environ.get('API_HOST') or str(yaml_cfg.get('api_host', ''))

    if not api_key or not api_host:
        print('Ошибка: необходимо задать API_KEY и API_HOST.')
        print('Используйте переменные окружения или config.yaml.')
        sys.exit(1)

    model = os.environ.get('MODEL') or str(yaml_cfg.get('model', 'gemma3'))

    limit_message = _parse_int(
        os.environ.get('LIMIT_MESSAGE') or str(yaml_cfg.get('limit_message', ''))
    )
    limit_chars = _parse_int(
        os.environ.get('LIMIT_CHARS') or str(yaml_cfg.get('limit_chars', ''))
    )
    temperature = _parse_float(
        os.environ.get('TEMPERATURE') or str(yaml_cfg.get('temperature', '')),
        default=0.7,
    )

    system_prompt_raw = os.environ.get('SYSTEM_PROMPT') or yaml_cfg.get('system_prompt')
    system_prompt = str(system_prompt_raw) if system_prompt_raw else None

    return Config(
        api_key=api_key,
        api_host=api_host,
        model=model,
        limit_message=limit_message,
        limit_chars=limit_chars,
        temperature=temperature,
        system_prompt=system_prompt,
    )
