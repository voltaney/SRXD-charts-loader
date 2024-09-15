"""flet GUIアプリケーションのエントリーポイント"""

from __future__ import annotations

import logging.config
import time
from logging import getLogger
from typing import TYPE_CHECKING

import flet as ft

import cache
from logger_config import load_logger_settings
from pages import FilterTab, SettingTab

if TYPE_CHECKING:
    pass

logger = getLogger(__name__)


def set_page_stat_from_cache(page: ft.Page) -> None:
    """キャッシュからウィンドウ情報を復元

    Args:
        page (ft.Page): ページオブジェクト
    """
    logger.info("キャッシュからアプリ情報を復元")
    user_envs = cache.load_cache()
    try:
        page.window.width = user_envs["window"]["width"]  # 幅
        page.window.height = user_envs["window"]["height"]  # 高さ
        page.window.left = user_envs["window"]["x"]  # 位置(LEFT)
        page.window.top = user_envs["window"]["y"]  # 位置(TOP)
    except KeyError:
        logger.info("キャッシュが見つからないため、デフォルト設定を適用")
        # デフォルト設定
        page.window.width = 800
        page.window.height = 800
        page.window.left = 100
        page.window.top = 100


def main(page: ft.Page) -> None:
    """fletアプリケーションのエントリーポイント

    Args:
        page (ft.Page): ページオブジェクト
    """
    load_logger_settings()
    # fletのログレベルを設定
    getLogger("flet_core").setLevel(logging.INFO)
    getLogger("flet_runtime").setLevel(logging.INFO)
    # キャッシュからウィンドウ情報を復元
    set_page_stat_from_cache(page)
    # ページの設定
    page.title = "Spinチャートローダー"
    page.theme = ft.Theme(
        color_scheme_seed="amber",
        # scrollbar_theme=ft.ScrollbarTheme(track_visibility=True),
        expansion_tile_theme=ft.ExpansionTileTheme(
            # bgcolor=ft.colors.PRIMARY_CONTAINER,
        ),
    )
    page.padding = ft.padding.all(0)
    # ウィンドウクローズイベントをキャッチできるようにする
    page.window.prevent_close = True

    def on_close(e: ft.WindowEvent) -> None:
        """ウィンドウが閉じられた際の処理"""
        if e.type != ft.WindowEventType.CLOSE:
            return
        window_cache = {
            "window": {
                "width": page.window.width,
                "height": page.window.height,
                "x": page.window.left,
                "y": page.window.top,
            },
        }
        ending_modal = ft.AlertDialog(
            modal=False,
            title=ft.Text("終了処理中"),
            content=ft.ProgressBar(),
        )
        page.open(ending_modal)
        time.sleep(0.5)
        cache.save_cache(window_cache)
        filter_tab.save_cache()
        page.window.destroy()

    # ウィンドウのイベントハンドラを設定
    page.window.on_event = on_close

    filter_tab = FilterTab()
    main_content = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(
                text="フィルター",
                content=filter_tab,
            ),
            ft.Tab(
                text="設定",
                icon=ft.icons.SETTINGS,
                content=SettingTab(),
            ),
        ],
        scrollable=True,
        expand=True,
    )

    page.add(main_content)


# アプリ実行
ft.app(main)
