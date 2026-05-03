"""nomiboy GBC 風カラーパレット。

仮の値。最終的な配色は DESIGN.md（Task 27）で確定する。

NOMIBOY_INVERT_COLORS=1 のとき、全色を NOT 反転して定義する。
これは Raspberry Pi + Waveshare 3.5inch RPi LCD (F) の組み合わせで、
SPI データパスの都合で表示が完全反転してしまうのを打ち消すための回避策。
PC で動かす際は環境変数を立てない（=デフォルトで通常色）。
"""
from __future__ import annotations

import os

INVERT_COLORS: bool = os.environ.get("NOMIBOY_INVERT_COLORS", "0") == "1"


def _inv(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    if INVERT_COLORS:
        r, g, b = rgb
        return (255 - r, 255 - g, 255 - b)
    return rgb


# 基本背景・前景
BG_PRIMARY: tuple[int, int, int] = _inv((255, 203, 5))        # 黄
BG_SECONDARY: tuple[int, int, int] = _inv((255, 119, 0))      # オレンジ
INK_DARK: tuple[int, int, int] = _inv((43, 10, 61))           # 紫黒
INK_LIGHT: tuple[int, int, int] = _inv((255, 255, 255))       # 白

# アクセント
ACCENT_BERRY: tuple[int, int, int] = _inv((176, 48, 96))      # ベリー
ACCENT_LIME: tuple[int, int, int] = _inv((155, 188, 15))      # DMG ライム

# プレイヤー4色（登録順にローテ割当）
PLAYER_COLORS: list[tuple[int, int, int]] = [
    _inv((220, 60, 60)),    # 赤
    _inv((60, 130, 220)),   # 青
    _inv((60, 190, 90)),    # 緑
    _inv((240, 200, 50)),   # 黄
]

# 警告
DANGER_RED: tuple[int, int, int] = _inv((220, 30, 30))
WARNING_AMBER: tuple[int, int, int] = _inv((240, 160, 0))


def player_color(index: int) -> tuple[int, int, int]:
    """プレイヤー番号（0始まり）から色を返す。4を超えたら循環。"""
    return PLAYER_COLORS[index % len(PLAYER_COLORS)]
