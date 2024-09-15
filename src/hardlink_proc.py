"""ハードリンク作成処理を行うモジュール"""

import glob
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Callable

import pywintypes
import win32file

import settings

logger = getLogger(__name__)
ALBUM_ART_FOLDER_NAME = "AlbumArt"
AUDIO_CLIP_FOLDER_NAME = "AudioClips"
ALBUM_ART_EXT = ["png"]
AUDIO_CLIP_EXT = ["ogg", "mp3"]


@dataclass
class Result:
    """ハードリンク作成の結果を格納するクラス

    Args:
        has_error (bool): エラーが発生したか
        error_message (str): エラーメッセージ
        success_creation_count (int): 成功したハードリンクの数
    """

    has_error: bool = False
    error_message: str = ""
    success_creation_count: int = 0


def create_hardlink(  # noqa: C901
    srtb_list: list[tuple[str, str, str]], on_each_creation: Callable[[int, int], None] | None = None
) -> Result:
    """ハードリンクを作成する関数

    Args:
        srtb_list (list[tuple[str, str, str]]): srtbファイルのリスト
        on_each_creation (Callable[[int, int], None] | None, optional): 各ハードリンク作成時に呼び出されるコールバック

    Returns:
        Result: ハードリンク作成の結果
    """
    result = Result()
    # パスの定義とフォルダの作成
    user_settings = settings.load_settings()
    source_custom_chart_dir = Path(user_settings.custom_charts_dir)
    hardlink_dir = Path(user_settings.hardlink_dir)
    source_album_art_dir = source_custom_chart_dir / ALBUM_ART_FOLDER_NAME
    source_clip_dir = source_custom_chart_dir / AUDIO_CLIP_FOLDER_NAME
    hardlink_album_art_dir = hardlink_dir / ALBUM_ART_FOLDER_NAME
    hardlink_clip_dir = hardlink_dir / AUDIO_CLIP_FOLDER_NAME
    hardlink_album_art_dir.mkdir(parents=True, exist_ok=True)
    hardlink_clip_dir.mkdir(parents=True, exist_ok=True)

    # すでにハードリンクとして存在する不要なファイルを削除
    delete_untargeted_hardlinks(srtb_list, hardlink_dir)
    # ハードリンク作成
    for idx, srtb in enumerate(srtb_list):
        if on_each_creation:
            on_each_creation(idx, len(srtb_list))
        srtb_stem, albumart_asset_name, clip_asset_name = srtb
        # srtbファイルのハードリンク作成
        src_srtb = source_custom_chart_dir / f"{srtb_stem}.srtb"
        dst_srtb = hardlink_dir / f"{srtb_stem}.srtb"
        try:
            win32file.CreateHardLink(str(dst_srtb.resolve()), str(src_srtb.resolve()))
        except pywintypes.error as e:
            if e.winerror == 2:
                # ソースファイルが存在しない
                logger.warning(f"ソースファイルが存在しないためスキップされました: {src_srtb.name}")
                continue
            elif e.winerror == 183:
                # すでにハードリンクが存在する
                logger.info(f"既にソースファイルが存在するためスキップされました: {src_srtb.name}")
                result.success_creation_count += 1
                continue
            elif e.winerror == 17:
                # 同じボリューム内でのみハードリンクが作成可能
                result.has_error = True
                result.error_message = "同じボリューム内でのみハードリンクが作成可能です。設定を見直してください"
                break
            else:
                # 再スロー
                logger.exception(f"ハードリンク作成に失敗: {e}")
                raise e
        # アルバムアートのハードリンク作成
        album_art_files = source_album_art_dir.glob(glob.escape(albumart_asset_name) + ".*")
        src_album_art_file = None
        for file in album_art_files:
            if file.is_file():
                src_album_art_file = file
                break
        if src_album_art_file is not None:
            dst_art = hardlink_album_art_dir / src_album_art_file.name
            try:
                win32file.CreateHardLink(str(dst_art.resolve()), str(src_album_art_file.resolve()))
            except pywintypes.error as e:
                print(dst_art.resolve())
                print(f"{src_album_art_file.resolve()}: {e}")
        else:
            logger.warning(f"画像ファイル「{albumart_asset_name}」が見つかりません")
        # クリップのハードリンク作成
        clip_files = source_clip_dir.glob(glob.escape(clip_asset_name) + ".*")
        src_clip_file = None
        for file in clip_files:
            if file.is_file():
                src_clip_file = file
                break
        if src_clip_file is not None:
            dst_clip = hardlink_clip_dir / src_clip_file.name
            win32file.CreateHardLink(str(dst_clip.resolve()), str(src_clip_file.resolve()))
        else:
            logger.warning(f"音声ファイル「{clip_asset_name}」が見つかりません")
        # 成功カウント
        result.success_creation_count += 1
    return result


def delete_untargeted_hardlinks(srtb_list: list[tuple[str, str, str]], hardlink_dir: Path) -> None:
    """ターゲット以外のハードリンクを削除する

    Args:
        srtb_list (list[tuple[str, str, str]]): ハードリンク作成対象のsrtbファイルのリスト
        hardlink_dir (Path): ハードリンクフォルダのパス
    """
    # srtbファイルの削除
    srtb_files = hardlink_dir.glob("*.srtb")

    targeted_srtb_stem = [srtb[0] for srtb in srtb_list]
    for file in srtb_files:
        if file.is_file() and file.stem not in targeted_srtb_stem:
            file.unlink()
    # アルバムアートの削除
    album_art_files = (hardlink_dir / ALBUM_ART_FOLDER_NAME).glob("*")
    targeted_album_art_name = [srtb[1] for srtb in srtb_list]
    for file in album_art_files:
        if file.is_file() and file.stem not in targeted_album_art_name:
            file.unlink()
    # クリップの削除
    clip_files = (hardlink_dir / AUDIO_CLIP_FOLDER_NAME).glob("*")
    targeted_clip_name = [srtb[2] for srtb in srtb_list]
    for file in clip_files:
        if file.is_file() and file.stem not in targeted_clip_name:
            file.unlink()
