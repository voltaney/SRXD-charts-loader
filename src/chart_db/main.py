"""Spin Rhythm XDのカスタムチャートの情報をSQLiteに保存するモジュール"""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from logging import getLogger
from pathlib import Path
from typing import Callable

import srtb

from .connection import get_db_connection

logger = getLogger(__name__)


@dataclass
class SearchCondition:
    """検索条件を格納するクラス

    Args:
        title (list[str] | None): 曲名
        artist (list[str] | None): アーティスト名
        charter (list[str] | None): チャーター名
        min_diff_level (str | None): 最小難易度
        max_diff_level (str | None): 最大難易度
        min_duration (str | None): 最小クリップ長さ
        max_duration (str | None): 最大クリップ長さ
        exclude_artist (list[str] | None): 除外するアーティスト名
        exclude_charter (list[str] | None): 除外するチャーター名
    """

    title: list[str] | None = None
    artist: list[str] | None = None
    charter: list[str] | None = None
    min_diff_level: str | None = None
    max_diff_level: str | None = None
    min_duration: str | None = None
    max_duration: str | None = None
    exclude_artist: list[str] | None = None
    exclude_charter: list[str] | None = None

    def generate_where_query(self) -> str:
        """検索条件からWHERE句を生成する

        Returns:
            str: WHERE句
        """
        conditions = []
        if self.title and self.title[0] != "":
            title_or_conditions = [f"track_title LIKE '%{title}%'" for title in self.title]
            conditions.append("(" + " OR ".join(title_or_conditions) + ")")
        if self.artist and self.artist[0] != "":
            artist_or_conditions = [f"track_artist LIKE '%{artist}%'" for artist in self.artist]
            conditions.append("(" + " OR ".join(artist_or_conditions) + ")")
        if self.charter and self.charter[0] != "":
            charter_or_conditions = [f"charter LIKE  '%{charter}%'" for charter in self.charter]
            conditions.append("(" + " OR ".join(charter_or_conditions) + ")")
        if self.min_diff_level:
            min_diff_or_conditions = []
            min_diff_or_conditions.append(f"easy_difficulty >= {self.min_diff_level}")
            min_diff_or_conditions.append(f"normal_difficulty >= {self.min_diff_level}")
            min_diff_or_conditions.append(f"hard_difficulty >= {self.min_diff_level}")
            min_diff_or_conditions.append(f"expert_difficulty >= {self.min_diff_level}")
            min_diff_or_conditions.append(f"xd_difficulty >= {self.min_diff_level}")
            conditions.append("(" + " OR ".join(min_diff_or_conditions) + ")")
        if self.max_diff_level:
            max_diff_or_conditions = []
            max_diff_or_conditions.append(f"easy_difficulty <= {self.max_diff_level}")
            max_diff_or_conditions.append(f"normal_difficulty <= {self.max_diff_level}")
            max_diff_or_conditions.append(f"hard_difficulty <= {self.max_diff_level}")
            max_diff_or_conditions.append(f"expert_difficulty <= {self.max_diff_level}")
            max_diff_or_conditions.append(f"xd_difficulty <= {self.max_diff_level}")
            conditions.append("(" + " OR ".join(max_diff_or_conditions) + ")")
        if self.min_duration:
            conditions.append(f"clip_duration >= {self.min_duration}")
        if self.max_duration:
            conditions.append(f"clip_duration <= {self.max_duration}")
        if self.exclude_artist:
            exclude_artist_or_conditions = [f"track_artist NOT LIKE '%{artist}%'" for artist in self.exclude_artist]
            conditions.append("(" + " AND ".join(exclude_artist_or_conditions) + ")")
        if self.exclude_charter:
            exclude_charter_or_conditions = [f"charter NOT LIKE '%{charter}%'" for charter in self.exclude_charter]
            conditions.append("(" + " AND ".join(exclude_charter_or_conditions) + ")")
        return " AND ".join(conditions)


def truncate_srtb_table() -> None:
    """srtbテーブルを初期化する"""
    conn = get_db_connection()
    with closing(conn):
        c = conn.cursor()
        c.execute("DELETE FROM srtb")
        conn.commit()


def get_latest_update_date() -> str:
    """最新更新日時を取得する

    Returns:
        str: 最新更新日時
    """
    conn = get_db_connection()
    with closing(conn):
        c = conn.cursor()
        c.execute("SELECT datetime(MAX(created_at), '+9 hours') FROM srtb")
        result = c.fetchone()
    return result[0] if result else ""


def search_file_reference(condition: SearchCondition) -> list[tuple[str, str, str]]:
    """検索条件に一致するチャートファイル情報を取得する

    Args:
        condition (SearchCondition): 検索条件

    Returns:
        list[tuple[str, str, str]]: ファイル参照名、アルバムアート名、クリップ名のリスト
    """
    conn = get_db_connection()
    with closing(conn):
        c = conn.cursor()
        # すべての条件を満たす行を取得
        query = "SELECT file_reference, albumart_asset_name, clip_asset_name FROM srtb"
        where_query = condition.generate_where_query()
        if where_query:
            query += " WHERE " + where_query
        c.execute(query)
        result = c.fetchall()
    return result


# srtb.loadで指定されたディレクトリ内のsrtbファイルをすべて読み込み、SQLLiteに保存する
def load_srtb_files_to_sqlite(
    custom_chart_dir: str, on_each_load: Callable[[srtb.Srtb, int, int], None] | None
) -> None:
    """指定されたディレクトリ内のsrtbファイルを読み込み、SQLiteに保存する

    Args:
        custom_chart_dir (str): カスタムチャートのディレクトリ
        on_each_load (Callable[[srtb.Srtb, int, int], None] | None): 各ファイル読み込み時に呼び出されるコールバック
    """

    def get_difficulty_value(difficulty: srtb.ChartDifficulty) -> int:
        return difficulty.level if difficulty.is_defined else None

    conn = get_db_connection()
    c = conn.cursor()
    chart_file_list = list(Path(custom_chart_dir).glob("*.srtb"))
    for idx, chart_file in enumerate(chart_file_list):
        file_modified_at = datetime.fromtimestamp(chart_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT file_modified_at FROM srtb WHERE file_reference = ?", (chart_file.stem,))
        result = c.fetchone()
        if result and result[0] == file_modified_at:
            # すでに読み込み済みで更新されていないファイルはスキップ
            continue
        try:
            with open(chart_file, "r", encoding="utf-8") as f:
                chart = srtb.load(f)
        except Exception:
            logger.exception(f"{chart_file.stem}の読み込みに失敗しました")
            continue
        # クリップの長さも読み込み
        chart.read_clip_metadata()
        # chart内容を書き込み
        # file_referenceが存在する場合は上書き
        c.execute(
            """
        INSERT OR REPLACE INTO srtb (
            file_reference,
            track_title, track_subtitle, track_artist, charter,
            easy_difficulty, normal_difficulty, hard_difficulty,
            expert_difficulty, xd_difficulty, albumart_asset_name,
            clip_asset_name, self_path, clip_duration,
            file_modified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
            (
                chart.file_reference,
                chart.track_title,
                chart.track_subtitle,
                chart.track_artist,
                chart.charter,
                get_difficulty_value(chart.easy_difficulty),
                get_difficulty_value(chart.normal_difficulty),
                get_difficulty_value(chart.hard_difficulty),
                get_difficulty_value(chart.expert_difficulty),
                get_difficulty_value(chart.xd_difficulty),
                chart.albumart_asset_name,
                chart.clip_asset_name,
                str(chart.self_path),
                chart.clip_duration,
                file_modified_at,
            ),
        )
        if on_each_load:
            on_each_load(chart, idx, len(chart_file_list))
        conn.commit()
    conn.close()
