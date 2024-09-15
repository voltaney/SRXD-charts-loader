"""ロガーの設定を行うモジュール"""

import logging.config


def load_logger_settings() -> None:
    """ロガーを設定"""
    logging.config.dictConfig(
        {
            "version": 1,
            "root": {"level": "DEBUG", "handlers": ["consoleHandler", "logFileHandler"]},
            "disable_existing_loggers": False,
            "handlers": {
                "consoleHandler": {"formatter": "rich", "class": "rich.logging.RichHandler", "level": "DEBUG"},
                "logFileHandler": {
                    "formatter": "logFileFormatter",
                    "mode": "w",
                    "encoding": "utf-8",
                    "level": "INFO",
                    "class": "logging.FileHandler",
                    "filename": "./app.log",
                },
            },
            "formatters": {
                "rich": {"datefmt": "[%X]", "format": "%(message)s"},
                "logFileFormatter": {"format": "[%(levelname)-7s:%(name)s] %(funcName)s -> %(message)s"},
            },
        }
    )
