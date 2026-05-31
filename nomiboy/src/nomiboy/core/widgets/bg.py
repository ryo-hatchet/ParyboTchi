"""背景画像のロード + 画面サイズへ aspect-fill。"""
from __future__ import annotations

import pygame

from nomiboy import colors


def load_background(ctx, rel_path: str, screen_size: tuple[int, int]) -> pygame.Surface:
    """ctx.assets から画像を読み、screen_size に aspect-fill + center crop。

    縦に潰れないよう短辺合わせで拡縮し、はみ出た部分をセンタートリミング。
    INVERT_COLORS が真なら NOT 反転も適用する。
    """
    sw, sh = screen_size
    raw = ctx.assets.image(rel_path)
    iw, ih = raw.get_width(), raw.get_height()
    src_ratio = iw / ih
    dst_ratio = sw / sh
    if src_ratio > dst_ratio:
        # 元画像の方が横長: 高さを合わせて横をトリミング
        new_h = sh
        new_w = int(sh * src_ratio)
    else:
        # 元画像の方が縦長: 横を合わせて高さをトリミング
        new_w = sw
        new_h = int(sw / src_ratio)
    scaled = pygame.transform.smoothscale(raw, (new_w, new_h))
    # 中央クロップ
    crop_x = (new_w - sw) // 2
    crop_y = (new_h - sh) // 2
    result = pygame.Surface(screen_size)
    result.blit(scaled, (-crop_x, -crop_y))
    if colors.INVERT_COLORS:
        inv = pygame.Surface(result.get_size())
        inv.fill((255, 255, 255))
        inv.blit(result, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        result = inv
    return result
