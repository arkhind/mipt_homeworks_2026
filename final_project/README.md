# GigaVibeMiptCode

Консольный ИИ-ассистент с поддержкой OpenAI-совместимых LLM.

## Функционал

- Чат с историей сообщений
- Контроль длины контекста (по количеству сообщений и символов)
- Конфигурация через переменные окружения или `config.yaml`
- Прерывание запроса к модели через `Ctrl+C`
- Прикрепление файлов к сообщению через `@::путь/к/файлу::`
- Почанковая обработка больших файлов (`/file_chunk`)
- Стриминг ответов модели в реальном времени
- Команды `/reset` и `\q`

## Установка

```bash
pip install -r requirements.txt
```

## Конфигурация

**Через переменные окружения** (приоритет над yaml):

```bash
export API_KEY=your_key_here
export API_HOST=http://localhost:11434/v1/
export MODEL=gemma3
export LIMIT_CHARS=2000
export LIMIT_MESSAGE=20
export TEMPERATURE=0.7
```

**Через `config.yaml`** (скопируйте из примера):

```bash
cp config.yaml config.yaml
# отредактируйте config.yaml
```

Формат файла:

```yaml
api_key: your_api_key_here
api_host: http://localhost:11434/v1/
model: gemma3
limit_message: 20
limit_chars: 2000
temperature: 0.7
system_prompt: You are a helpful assistant.
```

> `config.yaml` содержит секреты — он добавлен в `.gitignore`.

## Запуск

```bash
cd final_project
python main.py
```

## Команды

| Команда | Описание |
|---|---|
| `\q` | Выход из программы |
| `/reset` | Очистить историю и экран |
| `/file_chunk` | Обработать файл по абзацам |
| `/file_chunk paragraph=3` | По 3 абзаца за раз |
| `/file_chunk len=500` | По 500 символов за раз |
| `/file_chunk -y` | Авто-режим (без паузы между чанками) |
| `@::путь/к/файлу::` | Прикрепить содержимое файла к сообщению |

## Тесты

```bash
cd final_project
pytest --cov=. --cov-report=html
```

Отчёт о покрытии будет в папке `htmlcov/`.

## Локальная модель (Ollama)

```bash
# Установить Ollama: https://ollama.com/download
ollama pull gemma3:4b
```

Затем задать в конфиге:
```yaml
api_host: http://localhost:11434/v1/
model: gemma3:4b
api_key: ollama
```
