"""DB接続関連のモジュール"""

import sqlite3

_first_connection = True


def get_db_connection() -> sqlite3.Connection:
    """DB接続を取得する

    初回の呼び出し時にsrtbテーブルが存在しない場合は作成する

    Returns:
        sqlite3.Connection: DB接続
    """
    global _first_connection
    conn = sqlite3.connect("charts.db")
    if _first_connection:
        create_srtb_table_if_not_exists(conn)
        _first_connection = False  # フラグを更新して次回以降の呼び出しで処理が実行されないようにする

    return conn


def create_srtb_table_if_not_exists(conn: sqlite3.Connection) -> None:
    """srtbテーブルが存在しない場合は作成する

    Args:
        conn (sqlite3.Connection): DB接続
    """
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS srtb (
            file_reference TEXT PRIMARY KEY,
            track_title TEXT NOT NULL,
            track_subtitle TEXT,
            track_artist TEXT NOT NULL,
            charter TEXT NOT NULL,
            easy_difficulty INTEGER,
            normal_difficulty INTEGER,
            hard_difficulty INTEGER,
            expert_difficulty INTEGER,
            xd_difficulty INTEGER,
            albumart_asset_name TEXT NOT NULL,
            clip_asset_name TEXT NOT NULL,
            self_path TEXT NOT NULL,
            clip_duration INTEGER,
            file_modified_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
