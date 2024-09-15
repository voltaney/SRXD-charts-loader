"""チャートフィルタのをグループとして管理するためのモジュール

Fletコンポーネントとしての出力と、データの入出力を行う
"""

from __future__ import annotations

import abc
from typing import Any

import flet as ft

# フォームに関するスタイル
FORM_HEIGHT = 35
FORM_FONT_SIZE = 14
FORM_CONTENT_PADDING = ft.Padding(10, 0, 0, 0)
FORM_PANE_WIDTH = 500
FORM_PANE_PADDING = ft.Padding(15, 10, 15, 25)
FORM_SPACING = 2
FORM_LABEL_WIDTH = 130


class ChartFileterGroup:
    """チャートフィルタの条件のグループ"""

    def __init__(self, forms: list[FilterOptionForm]) -> None:
        """チャートフィルタのグループを作成する

        Args:
            forms (list[FilterOptionForm]): 使用するFilterOptionForm
        """
        self.forms = forms

    def create_view(self, title: str, subtitle: str | None = None, color: str | None = None) -> ft.ExpansionTile:
        """Flet用のViewを作成

        Returns:
            ft.ExpansionTile: Flet用のView
        """
        filter_group = ft.Column(
            controls=self.forms,
            spacing=FORM_SPACING,
            width=FORM_PANE_WIDTH,
        )

        def update_initially_expanded(e: ft.ControlEvent) -> None:
            # ExpansionTileの開閉状態を更新
            # tabの切り替えでリセットされるため
            tile.initially_expanded = not tile.initially_expanded
            tile.update()

        tile = ft.ExpansionTile(
            title=ft.Text(title, size=18, weight=ft.FontWeight.W_500),
            subtitle=ft.Text(subtitle, size=12),
            affinity=ft.TileAffinity.LEADING,
            maintain_state=True,
            collapsed_text_color=color,
            text_color=color,
            initially_expanded=True,
            controls=[filter_group],
            visual_density=ft.VisualDensity.COMPACT,
            on_change=update_initially_expanded,
            controls_padding=FORM_PANE_PADDING,
            expanded_alignment=ft.alignment.top_left,
        )
        return tile

    def values(self) -> dict[str, str]:
        """フィルターの値を取得する

        Returns:
            dict[str, str]: フィルターの値
        """
        values = {}
        for form in self.forms:
            values[form.filter_id] = form.value() if form.is_enabled() else None
        return values

    def load_values(self, values: dict) -> None:
        """フィルターの値をロードする

        Args:
            values (dict): フィルターの値
        """
        for form in self.forms:
            if form.filter_id in values:
                form.checkbox.value = values[form.filter_id] is not None
                if values[form.filter_id] is not None:
                    form.load_value(values[form.filter_id])


class FilterOptionForm(ft.Row, metaclass=abc.ABCMeta):
    """フィルタオプション用のFletコンポーネントの基底クラス"""

    def __init__(self, id: str, label: str):
        """コンストラクタ

        Args:
            id (str): フィルターID。データの入出力に使用
            label (str): フィルターのラベル。Fletコンポーネントの表示に使用
        """
        super().__init__()
        self.checkbox = ft.Checkbox(
            label=label,
            width=FORM_LABEL_WIDTH,
        )
        self.filter_id = id
        self.controls = [self.checkbox]

    def is_enabled(self) -> bool:
        """フィルターが有効かどうかを返す

        Returns:
            bool: フィルターが有効かどうか
        """
        return self.checkbox.value

    @abc.abstractmethod
    def value(self) -> Any:
        """フィルターの値を返す

        Returns:
            T: フィルターの値
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load_value(self, value: Any) -> None:
        """フィルターの値をロードする

        Args:
            value (T): フィルターの値
        """
        raise NotImplementedError


class TextFilterOptionForm(FilterOptionForm):
    """TextFieldフィルタオプション用のFletコンポーネント"""

    def __init__(
        self,
        id: str,
        label: str,
        text_field_width: int | None = None,
        only_integer_input: bool = False,
        comma_split: bool = False,
    ):
        """コンストラクタ

        Args:
            id (str): フィルターID
            label (str): フィルターのラベル
            text_field_width (int | None, optional): テキストフィールドの幅。Defaults to None.
            only_integer_input (bool, optional): テキストフィールドの入力を整数に制限。 Defaults to False.
            comma_split (bool, optional): カンマ区切りにして、リストデータとして扱うか。 Defaults to False.
        """
        super().__init__(id, label)
        self.text_field = ft.TextField(
            text_size=FORM_FONT_SIZE,
            height=FORM_HEIGHT,
            width=text_field_width,
            expand=True,
            content_padding=FORM_CONTENT_PADDING,
            input_filter=ft.NumbersOnlyInputFilter() if only_integer_input else None,
        )
        self.controls.append(self.text_field)
        self.comma_split = comma_split

    def value(self) -> str | list[str] | None:
        """フィルターの値を返す

        Returns:
            str: フィルターの値
        """
        # Noneではなく、カンマ区切りが有効な場合はリストで返す
        if self.comma_split and self.text_field.value is not None:
            return self.text_field.value.split(",")
        return self.text_field.value

    def load_value(self, value: str | list[str] | None) -> None:
        """フィルターの値をロードする

        Args:
            value (str | list[str] | None): フィルターの値
        """
        if value is not None:
            if self.comma_split:
                self.text_field.value = ",".join(value)
            else:
                self.text_field.value = value


class DropdownFilterOptionForm(FilterOptionForm):
    """Dropdown形式のフィルタオプション用のFletコンポーネント"""

    def __init__(self, id: str, label: str, options: list[ft.dropdown.Option]):
        """コンストラクタ

        Args:
            id (str): フィルターID
            label (str): フィルターのラベル
            options (list[ft.dropdown.Option]): ドロップダウンの選択肢
        """
        super().__init__(id, label)
        self.dropdown = ft.Dropdown(
            options=options,
            # selected_index=0,
            expand=True,
            height=FORM_HEIGHT,
            text_size=FORM_FONT_SIZE,
            content_padding=FORM_CONTENT_PADDING,
        )
        self.controls.append(self.dropdown)

    def value(self) -> str:
        """フィルターの値を返す

        Returns:
            str: フィルターの値
        """
        return self.dropdown.value

    def load_value(self, value: str) -> None:
        """フィルターの値をロードする

        Args:
            value (str): フィルターの値
        """
        self.dropdown.value = value
