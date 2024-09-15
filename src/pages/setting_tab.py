"""設定タブ画面を提供するモジュール"""

from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import flet as ft

import chart_db
import settings

if TYPE_CHECKING:
    import srtb
logger = getLogger(__name__)


class SettingTab(ft.Container):
    """設定タブ画面"""

    def __init__(self) -> None:
        """設定タブ画面を作成する"""
        super().__init__()

        self.content = ft.Column(
            controls=[
                DatabasePane(),
                ft.Divider(color=ft.colors.BROWN_500),
                PathPane(),
            ],
            scroll=ft.ScrollMode.AUTO,
        )
        self.padding = ft.padding.symmetric(20, 20)


class DatabasePane(ft.Column):
    """データベースに関する設定画面"""

    def __init__(self) -> None:
        """データベースに関する設定画面を作成する"""
        super().__init__()
        self.latest_load_date = ft.TextSpan(chart_db.get_latest_update_date())
        self.progress_bar = ft.ProgressBar()
        self.progress_text = ft.Text(size=12)
        self.progress_info = ft.Column(
            controls=[
                self.progress_bar,
                self.progress_text,
            ],
            visible=False,
        )
        self.load_button = ft.TextButton("ロード", icon=ft.icons.SAVE, on_click=self.on_load_chart_data)
        self.truncate_button = ft.TextButton(
            "データベースの初期化",
            style=ft.ButtonStyle(color=ft.colors.RED),
            icon=ft.icons.DELETE,
            on_click=self.on_click_truncate_button,
        )
        self.controls = [
            ft.Text("チャートデータのロード", size=25),
            ft.Text(
                "カスタムチャートを読み込んでデータベースを作成します。更新が必要なファイルのみ読み込まれます。",
                size=14,
            ),
            ft.Text(
                spans=[
                    ft.TextSpan("最終更新チェック: "),
                    self.latest_load_date,
                    ft.TextSpan("（更新がない場合は変化しません）"),
                ],
                size=14,
            ),
            self.progress_info,
            ft.Row(
                controls=[
                    self.load_button,
                    self.truncate_button,
                ]
            ),
        ]

    def on_load_chart_data(self, e: ft.ControlEvent) -> None:
        """チャートデータをロードする

        Args:
            e (ft.ControlEvent): イベント情報
        """
        logger.info("チャートデータのロードを開始")
        # ロード状況を表示 / ロードボタンを無効化
        self.progress_info.visible = True
        self.load_button.disabled = True
        self.update()
        user_settings = settings.load_settings()
        chart_db.load_srtb_files_to_sqlite(user_settings.custom_charts_dir, on_each_load=self.on_each_chart_load)
        logger.info("チャートデータのロードが完了")
        self.latest_load_date.text = chart_db.get_latest_update_date()
        snackbar = ft.SnackBar(content=ft.Text("チャートデータをロードしました"), duration=3000)
        self.page.overlay.append(snackbar)
        snackbar.open = True
        # ロード状況を非表示 / ロードボタンを有効化
        self.progress_info.visible = False
        self.load_button.disabled = False
        self.page.update()

    def on_each_chart_load(self, srtb: srtb.Srtb, idx: int, total: int) -> None:
        """チャートデータをロードする際のコールバック関数

        Args:
            srtb (srtb.Srtb): srtbデータ
            idx (int): コールバックの呼び出し回数
            total (int): ロードするファイル数
        """
        self.progress_bar.value = idx / total
        self.progress_text.value = f"{idx}/{total} ファイルをロード中"
        self.update()

    def on_click_truncate_button(self, e: ft.ControlEvent) -> None:
        """データベースを初期化するボタンをクリックされた際のコールバック関数

        Args:
            e (ft.ControlEvent): イベント情報
        """
        self.truncate_button.disabled = True
        self.update()
        self.page.update()
        chart_db.truncate_srtb_table()
        logger.info("データベースの初期化を完了")
        self.truncate_button.disabled = False
        snackbar = ft.SnackBar(content=ft.Text("データベースを初期化しました"), duration=3000)
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()


class PathPane(ft.Column):
    """パスに関する設定画面"""

    def __init__(self) -> None:
        """パスに関する設定画面を作成する"""
        super().__init__()
        user_settings = settings.load_settings()
        self.custom_chart_dir_text_field = ft.TextField(value=user_settings.custom_charts_dir)
        self.hardlink_dir_text_field = ft.TextField(value=user_settings.hardlink_dir)
        self.controls = [
            ft.Text("パス設定", size=25),
            ft.Text(
                "ハードリンクなんでどちらも同じボリュームじゃないと、動作しないっす！NTFSじゃないのも多分厳しいっす！",
                size=14,
                spans=[
                    ft.TextSpan(
                        "※ハードリンク",
                        ft.TextStyle(decoration=ft.TextDecoration.UNDERLINE),
                        url="https://e-words.jp/w/%E3%83%8F%E3%83%BC%E3%83%89%E3%83%AA%E3%83%B3%E3%82%AF.html",
                    ),
                ],
            ),
            ft.Text("カスタムチャートフォルダ", size=17),
            self.custom_chart_dir_text_field,
            ft.Text("ハードリンク作成先", size=17),
            self.hardlink_dir_text_field,
            ft.Row(
                controls=[
                    ft.TextButton("保存", icon=ft.icons.SAVE, on_click=self.on_save_settings),
                    ft.TextButton(
                        "デフォルトに戻す",
                        icon=ft.icons.SETTINGS_BACKUP_RESTORE,
                        on_click=self.on_save_default_settings,
                    ),
                ]
            ),
        ]

    def on_save_settings(self, e: ft.ControlEvent) -> None:
        """設定保存ボタンをクリックされた際のコールバック関数

        Args:
            e (ft.ControlEvent): イベント情報
        """
        new_settings = settings.Settings(
            custom_charts_dir=self.custom_chart_dir_text_field.value, hardlink_dir=self.hardlink_dir_text_field.value
        )
        settings.save_settings(new_settings)
        logger.info("パス設定を保存")
        self.reload_settings_text_field()
        snackbar = ft.SnackBar(content=ft.Text("設定を保存しました"), duration=3000)
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def on_save_default_settings(self, e: ft.ControlEvent) -> None:
        """デフォルト設定に戻すボタンをクリックされた際のコールバック関数

        Args:
            e (ft.ControlEvent): イベント情報
        """
        settings.save_default_settings()
        self.reload_settings_text_field()
        snackbar = ft.SnackBar(content=ft.Text("デフォルト設定に戻しました"), duration=3000)
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def reload_settings_text_field(self) -> None:
        """設定ファイルを読み込んでテキストフィールドに設定する"""
        user_settings = settings.load_settings()
        self.custom_chart_dir_text_field.value = user_settings.custom_charts_dir
        self.hardlink_dir_text_field.value = user_settings.hardlink_dir
