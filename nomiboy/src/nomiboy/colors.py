"""nomiboy GBC 風カラーパレット。

仮の値。最終的な配色は DESIGN.md（Task 27）で確定する。
"""
from __future__ import annotations

# 基本背景・前景
BG_PRIMARY: tuple[int, int, int] = (255, 203, 5)        # 黄
BG_SECONDARY: tuple[int, int, int] = (255, 119, 0)      # オレンジ
INK_DARK: tuple[int, int, int] = (43, 10, 61)           # 紫黒
INK_LIGHT: tuple[int, int, int] = (255, 255, 255)       # 白

# アクセント
ACCENT_BERRY: tuple[int, int, int] = (176, 48, 96)      # ベリー
ACCENT_LIME: tuple[int, int, int] = (155, 188, 15)      # DMG ライム

# プレイヤー4色（登録順にローテ割当）
PLAYER_COLORS: list[tuple[int, int, int]] = [
    (220, 60, 60),    # 赤
    (60, 130, 220),   # 青
    (60, 190, 90),    # 緑
    (240, 200, 50),   # 黄
]

# 警告
DANGER_RED: tuple[int, int, int] = (220, 30, 30)
WARNING_AMBER: tuple[int, int, int] = (240, 160, 0)


def player_color(index: int) -> tuple[int, int, int]:
    """プレイヤー番号（0始まり）から色を返す。4を超えたら循環。"""
    return PLAYER_COLORS[index % len(PLAYER_COLORS)]
