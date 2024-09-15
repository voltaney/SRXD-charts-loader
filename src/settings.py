"""設定ファイルのREAD/WRITEを提供するモジュール"""

import os
from dataclasses import asdict, dataclass
from pathlib import Path

import toml

# 設定ファイルのパス
SETTINGS_PATH = "settings.toml"


@dataclass(kw_only=True)
class Settings:
    """設定ファイルの内容を保持するデータクラス

    Args:
        custom_charts_dir (str): カスタムチャートフォルダのパス
        hardlink_dir (str): ハードリンク作成先のパス
    """

    custom_charts_dir: str
    hardlink_dir: str


def load_settings() -> Settings:
    """設定ファイルを読み込む関数"""
    if not os.path.exists(SETTINGS_PATH):
        save_default_settings()
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            dict_settings = toml.load(f)
        try:
            return Settings(**dict_settings)
        except TypeError as e:
            raise ValueError("設定ファイルの形式が正しくありません") from e
    else:
        raise FileNotFoundError("設定ファイルが見つかりません")


def save_settings(new_setting: Settings) -> None:
    """設定ファイルに書き込む関数"""
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        toml.dump(asdict(new_setting), f)


def save_default_settings() -> None:
    """デフォルトの設定ファイルを保存する関数"""
    app_data_path = os.getenv("APPDATA")
    if app_data_path is None:
        raise ValueError("環境変数APPDATAが見つかりません")
    custom_charts_dir = Path(app_data_path) / r"..\LocalLow\Super Spin Digital\Spin Rhythm XD\Custom"
    hardlink_dir = Path("./chart_hardlinks")
    hardlink_dir.mkdir(parents=True, exist_ok=True)
    default_setting = Settings(
        custom_charts_dir=str(custom_charts_dir.resolve()),
        hardlink_dir=str(
            hardlink_dir.resolve(),
        ),
    )
    save_settings(default_setting)
