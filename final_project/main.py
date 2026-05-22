from app import App
from config import load_config


def main() -> None:
    config = load_config()
    App(config).run()


if __name__ == '__main__':
    main()
