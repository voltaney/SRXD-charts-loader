"""フィルタタブ画面を提供するモジュール"""

from logging import getLogger

import flet as ft

import cache
import chart_db
import hardlink_proc
from components.filter_options import ChartFileterGroup, DropdownFilterOptionForm, TextFilterOptionForm

logger = getLogger(__name__)


def search_charts_from_filter_values(filter_values: dict) -> list[tuple[str, str, str]]:
    """フィルタ条件に一致するチャートファイル情報のリストを取得する

    Args:
        filter_values (dict): フィルタ条件

    Returns:
        list[tuple[str, str, str]]: フィルタ条件に一致するチャートファイル情報のリスト
    """
    search_condition = chart_db.SearchCondition(**filter_values)
    return chart_db.search_file_reference(search_condition)


class FilterTab(ft.Container):
    """フィルタタブ画面"""

    POSITIVE_FILTER_CACHE_KEY = "positive_filter"
    NEGATIVE_FILTER_CACHE_KEY = "negative_filter"

    def __init__(self) -> None:
        """フィルタタブ画面を作成する"""
        super().__init__()
        self.init_chart_filter_groups()
        self.hardlink_creation_button = ft.ElevatedButton(
            "ハードリンク作成",
            on_click=self.on_click_hardlink_creation_button,
            icon=ft.icons.SYNC,
        )
        self.hardlink_progress_bar = ft.ProgressBar()
        self.hardlink_progress_text = ft.Text(size=12)
        self.hardlink_progress_info = ft.Column(
            controls=[
                self.hardlink_progress_bar,
                self.hardlink_progress_text,
            ],
            visible=False,
        )

        self.content = ft.Column(
            controls=[
                ft.Column(
                    controls=[
                        self.positive_fliter.create_view("プラス条件", "検索に含める条件"),
                        self.negative_filter.create_view("マイナス条件", "検索から除外する条件"),
                    ],
                    spacing=0,
                ),
                ft.Row(
                    controls=[
                        self.hardlink_creation_button,
                        ft.ElevatedButton(
                            "該当件数カウント",
                            on_click=self.on_click_check_count_button,
                            icon=ft.icons.CONFIRMATION_NUMBER_OUTLINED,
                        ),
                        ft.ElevatedButton(
                            "ハードリンクをクリア",
                            on_click=self.on_click_clear_hardlink_button,
                            style=ft.ButtonStyle(color=ft.colors.RED_300),
                            icon=ft.icons.DELETE,
                        ),
                    ]
                ),
                self.hardlink_progress_info,
            ],
            spacing=20,
            scroll=ft.ScrollMode.ALWAYS,
        )

        self.padding = ft.Padding(10, 0, 10, 10)

    def on_click_hardlink_creation_button(self, e: ft.ControlEvent) -> None:
        """ハードリンク作成ボタンがクリックされたときのコールバック関数

        Args:
            e (ft.ControlEvent): イベント情報
        """
        self.hardlink_progress_info.visible = True
        self.hardlink_creation_button.disabled = True
        self.page.update()
        search_result = search_charts_from_filter_values(self.positive_fliter.values() | self.negative_filter.values())
        logger.info("ハードリンク作成開始: %d 件", len(search_result))
        result = hardlink_proc.create_hardlink(search_result, on_each_creation=self.on_each_hardlink_creation)
        logger.info("ハードリンク作成結果: %s", result)

        self.hardlink_progress_info.visible = False
        self.hardlink_creation_button.disabled = False
        if result.has_error:
            snackbar = ft.SnackBar(
                content=ft.Text(f"{result.error_message}"),
                duration=3000,
            )
        else:
            snackbar = ft.SnackBar(
                content=ft.Text(
                    f"{result.success_creation_count}/{len(search_result)} 件のハードリンクが作成されました"
                ),
                duration=3000,
            )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def on_each_hardlink_creation(self, idx: int, total: int) -> None:
        """各ハードリンク作成時のコールバック関数

        Args:
            idx (int): 呼び出し回数
            total (int): ハードリンク作成するファイル総数
        """
        self.hardlink_progress_bar.value = float(idx) / total
        self.hardlink_progress_text.value = f"({idx}/{total}) ハードリンクを作成中..."
        self.page.update()

    def on_click_check_count_button(self, e: ft.ControlEvent) -> None:
        """件数カウントボタンがクリックされたときのコールバック関数

        Args:
            e (ft.ControlEvent): イベント情報
        """
        logger.info("該当件数カウント開始")
        search_result = search_charts_from_filter_values(self.positive_fliter.values() | self.negative_filter.values())
        logger.info("該当件数カウント完了: %d 件", len(search_result))
        snackbar = ft.SnackBar(content=ft.Text(f"{len(search_result)}件が該当します"), duration=3000)
        self.page.open(snackbar)

    def on_click_clear_hardlink_button(self, e: ft.ControlEvent) -> None:
        """ハードリンクをクリアするボタンがクリックされたときのコールバック関数

        Args:
            e (ft.ControlEvent): イベント情報
        """
        logger.info("ハードリンクの削除開始")
        hardlink_proc.delete_all_hardlinks()
        logger.info("ハードリンクの削除完了")
        snackbar = ft.SnackBar(content=ft.Text("ハードリンクを削除しました"), duration=3000)
        self.page.open(snackbar)

    def init_chart_filter_groups(self) -> None:
        """チャートフィルタのグループを初期化"""
        self.positive_fliter = ChartFileterGroup(
            forms=[
                TextFilterOptionForm(id="title", label="タイトル", comma_split=True),
                TextFilterOptionForm(id="artist", label="アーティスト", comma_split=True),
                TextFilterOptionForm(id="charter", label="チャーター", comma_split=True),
                TextFilterOptionForm(id="min_diff_level", label="最小難易度", only_integer_input=True),
                TextFilterOptionForm(id="max_diff_level", label="最大難易度", only_integer_input=True),
                DropdownFilterOptionForm(
                    "min_duration",
                    label="最短再生時間",
                    options=[
                        ft.dropdown.Option(key=f"{i}", text=f"{i//60}分{i%60}秒") for i in range(0, 60 * 7 + 1, 30)
                    ],
                ),
                DropdownFilterOptionForm(
                    "max_duration",
                    label="最長再生時間",
                    options=[
                        ft.dropdown.Option(key=f"{i}", text=f"{i//60}分{i%60}秒") for i in range(0, 60 * 7 + 1, 30)
                    ],
                ),
            ],
        )
        self.negative_filter = ChartFileterGroup(
            forms=[
                TextFilterOptionForm(id="exclude_artist", label="アーティスト", comma_split=True),
                TextFilterOptionForm(id="exclude_charter", label="チャーター", comma_split=True),
            ],
        )
        filter_cache = cache.load_cache()
        try:
            self.positive_fliter.load_values(filter_cache["positive_filter"])
            self.negative_filter.load_values(filter_cache["negative_filter"])
        except KeyError:
            pass

    def will_unmount(self) -> None:
        """アプリケーションが終了する際の処理

        厳密にはpageのコントロールから削除された場合に呼び出されるが、アプリ終了時にpage側でこの処理を強制している
        """
        super().will_unmount()
        cache.save_cache(
            {"positive_filter": self.positive_fliter.values(), "negative_filter": self.negative_filter.values()}
        )

    def save_cache(self) -> None:
        """フィルタ条件をキャッシュに保存"""
        cache.save_cache(
            {"positive_filter": self.positive_fliter.values(), "negative_filter": self.negative_filter.values()}
        )
