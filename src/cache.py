"""キャッシュファイルの読み込みと保存を行うモジュール"""

import os
from logging import getLogger

import toml

logger = getLogger(__name__)
CACHE_PATH = "cache.toml"


def load_cache() -> dict:
    """実行環境ファイルを読み込む関数"""
    logger.debug("キャッシュファイルの読み込み")
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as file:
            return toml.load(file)
    else:
        return {}


def save_cache(settings: dict) -> None:
    """設定ファイルに書き込む関数"""
    current_cache = load_cache()
    with open(CACHE_PATH, "w", encoding="utf-8") as file:
        toml.dump(current_cache | settings, file)
    logger.debug("キャッシュファイルの保存")
