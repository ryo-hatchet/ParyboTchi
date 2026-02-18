"""ParyboTchi - アーカイブUI画面（集めた曲一覧）"""

import pygame

from config import (
    SCREEN_SIZE, SCREEN_CENTER, BG_COLOR, WHITE, BLACK, GRAY, DARK_GRAY,
    ACCENT_COLOR, TEXT_COLOR, TITLE_COLOR, ARTIST_COLOR, LIGHT_GRAY,
)
from fonts import find_jp_font


class ArchiveScreen:
    """アーカイブ画面：集めた曲のリスト表示"""

    def __init__(self):
        font_path = find_jp_font()
        self.font_title = pygame.font.Font(font_path, 16)
        self.font_item = pygame.font.Font(font_path, 13)
        self.font_small = pygame.font.Font(font_path, 10)
        self.scroll_offset = 0
        self.item_height = 42
        self.max_visible = 4

    def scroll_down(self, total_songs):
        """1つ下にスクロール"""
        max_offset = max(0, total_songs - self.max_visible)
        self.scroll_offset = min(self.scroll_offset + 1, max_offset)

    def scroll_up(self):
        """1つ上にスクロール"""
        self.scroll_offset = max(0, self.scroll_offset - 1)

    def reset_scroll(self):
        """スクロール位置をリセット"""
        self.scroll_offset = 0

    def draw(self, surface, collection):
        """アーカイブ画面を描画"""
        surface.fill(BLACK)
        pygame.draw.circle(surface, BG_COLOR, (SCREEN_CENTER, SCREEN_CENTER), SCREEN_CENTER)

        # タイトル
        title = self.font_title.render(
            f"おんがく図鑑 ({collection.count})", True, ACCENT_COLOR,
        )
        title_rect = title.get_rect(centerx=SCREEN_CENTER, top=18)
        surface.blit(title, title_rect)

        if collection.count == 0:
            empty_text = self.font_item.render("まだないよ…", True, GRAY)
            empty_rect = empty_text.get_rect(center=(SCREEN_CENTER, SCREEN_CENTER))
            surface.blit(empty_text, empty_rect)

            hint = self.font_small.render("Aボタンで曲をきこう！", True, GRAY)
            hint_rect = hint.get_rect(centerx=SCREEN_CENTER, top=SCREEN_CENTER + 20)
            surface.blit(hint, hint_rect)
            return

        # 曲リスト（新しい曲が上）
        songs = list(reversed(collection.songs))
        list_top = 45
        list_bottom = SCREEN_SIZE - 35

        for i in range(self.max_visible):
            idx = self.scroll_offset + i
            if idx >= len(songs):
                break

            song = songs[idx]
            y = list_top + i * self.item_height

            # 項目背景
            item_rect = pygame.Rect(25, y, SCREEN_SIZE - 50, self.item_height - 4)
            pygame.draw.rect(surface, DARK_GRAY, item_rect, border_radius=6)

            # 番号
            num = len(songs) - idx
            num_text = self.font_small.render(f"#{num}", True, GRAY)
            surface.blit(num_text, (32, y + 4))

            # 曲名
            title_str = song["title"]
            if len(title_str) > 14:
                title_str = title_str[:13] + "…"
            song_title = self.font_item.render(title_str, True, TITLE_COLOR)
            surface.blit(song_title, (55, y + 3))

            # アーティスト名
            artist_str = song["artist"]
            if len(artist_str) > 16:
                artist_str = artist_str[:15] + "…"
            artist = self.font_small.render(artist_str, True, ARTIST_COLOR)
            surface.blit(artist, (55, y + 22))

        # スクロールインジケータ
        total = len(songs)
        if total > self.max_visible:
            self._draw_scrollbar(surface, total, list_top, list_bottom)

        # 操作ヒント
        hint = self.font_small.render("A:スクロール B:もどる", True, GRAY)
        hint_rect = hint.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 18)
        surface.blit(hint, hint_rect)

    def _draw_scrollbar(self, surface, total, top, bottom):
        """スクロールバーを描画"""
        bar_h = bottom - top
        bar_x = SCREEN_SIZE - 18
        pygame.draw.line(surface, DARK_GRAY, (bar_x, top), (bar_x, bottom), 2)

        thumb_h = max(10, int(bar_h * self.max_visible / total))
        max_offset = total - self.max_visible
        if max_offset > 0:
            thumb_y = top + int((bar_h - thumb_h) * self.scroll_offset / max_offset)
        else:
            thumb_y = top
        pygame.draw.rect(surface, ACCENT_COLOR, (bar_x - 2, thumb_y, 6, thumb_h), border_radius=3)
