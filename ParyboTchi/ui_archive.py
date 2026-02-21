"""ParyboTchi - アーカイブUI画面（2段構成: レベル情報 + 曲リスト）"""

import pygame

from config import (
    SCREEN_SIZE, SCREEN_CENTER, BG_COLOR, WHITE, BLACK, GRAY, DARK_GRAY,
    ACCENT_COLOR, TEXT_COLOR, TITLE_COLOR, ARTIST_COLOR, LIGHT_GRAY,
    GROWTH_STAGES, STAGE_TITLES,
)
from fonts import find_jp_font


# 上段・下段の境界Y座標
_DIVIDER_Y = 120


class ArchiveScreen:
    """アーカイブ画面：2段構成
    上段 (Y=0〜120):  ステージ名・称号・曲数・プログレスバー
    下段 (Y=120〜240): 曲リスト（スクロール可）
    """

    def __init__(self):
        font_path = find_jp_font()
        self.font_stage  = pygame.font.Font(font_path, 16)  # ステージ名
        self.font_title_h = pygame.font.Font(font_path, 13) # 称号・ラベル
        self.font_item   = pygame.font.Font(font_path, 15)  # 曲名
        self.font_small  = pygame.font.Font(font_path, 12)  # アーティスト・ヒント
        self.scroll_offset = 0
        self.item_height = 32
        self.max_visible = 3  # 下段に表示できる最大曲数

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

        self._draw_upper(surface, collection)
        self._draw_divider(surface)
        self._draw_lower(surface, collection)

    def _draw_upper(self, surface, collection):
        """上段: ステージ情報（レベル・称号・プログレスバー）"""
        stage = collection.get_growth_stage()
        next_stage, remaining = collection.get_next_stage()
        stage_name = stage["name"]
        title_str = STAGE_TITLES.get(stage_name, stage_name)

        # ステージ名（大きめ）
        stage_surf = self.font_stage.render(stage_name, True, ACCENT_COLOR)
        stage_rect = stage_surf.get_rect(centerx=SCREEN_CENTER, top=18)
        surface.blit(stage_surf, stage_rect)

        # 称号テキスト
        title_surf = self.font_title_h.render(f"《 {title_str} 》", True, LIGHT_GRAY)
        title_rect = title_surf.get_rect(centerx=SCREEN_CENTER, top=38)
        surface.blit(title_surf, title_rect)

        # 曲数
        count_surf = self.font_small.render(f"{collection.count}曲コレクション中", True, GRAY)
        count_rect = count_surf.get_rect(centerx=SCREEN_CENTER, top=55)
        surface.blit(count_surf, count_rect)

        # プログレスバー（次のステージへの進捗）
        bar_w = 160
        bar_h = 8
        bar_x = SCREEN_CENTER - bar_w // 2
        bar_y = 70

        if next_stage:
            # 現在ステージのmin_songsから次ステージのmin_songsまでの進捗
            current_min = stage["min_songs"]
            next_min = next_stage["min_songs"]
            progress = (collection.count - current_min) / max(1, next_min - current_min)
            progress = min(1.0, max(0.0, progress))

            # バー背景
            pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            # バー進捗
            fill_w = int(bar_w * progress)
            if fill_w > 0:
                pygame.draw.rect(surface, ACCENT_COLOR, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

            # 残り曲数ラベル（右寄せ）
            next_label = self.font_small.render(f"あと{remaining}曲 → {next_stage['name']}", True, GRAY)
            next_rect = next_label.get_rect(centerx=SCREEN_CENTER, top=82)
            surface.blit(next_label, next_rect)
        else:
            # マスター達成
            pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            pygame.draw.rect(surface, ACCENT_COLOR, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            max_surf = self.font_small.render("MAX！伝説のコレクター", True, ACCENT_COLOR)
            max_rect = max_surf.get_rect(centerx=SCREEN_CENTER, top=82)
            surface.blit(max_surf, max_rect)

        # 操作ヒント
        hint_surf = self.font_small.render("↓スワイプ：スクロール  右スワイプ：もどる", True, DARK_GRAY)
        hint_rect = hint_surf.get_rect(centerx=SCREEN_CENTER, top=102)
        surface.blit(hint_surf, hint_rect)

    def _draw_divider(self, surface):
        """上段・下段の区切り線"""
        pygame.draw.line(surface, DARK_GRAY,
                         (30, _DIVIDER_Y), (SCREEN_SIZE - 30, _DIVIDER_Y), 1)

    def _draw_lower(self, surface, collection):
        """下段: 曲リスト（新しい曲が上）"""
        if collection.count == 0:
            empty_text = self.font_item.render("まだないよ…", True, GRAY)
            empty_rect = empty_text.get_rect(centerx=SCREEN_CENTER, centery=(_DIVIDER_Y + SCREEN_SIZE) // 2)
            surface.blit(empty_text, empty_rect)
            return

        songs = list(reversed(collection.songs))
        list_top = _DIVIDER_Y + 4
        list_bottom = SCREEN_SIZE - 8

        # クリッピング（上段にはみ出さない）
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(0, _DIVIDER_Y, SCREEN_SIZE, SCREEN_SIZE - _DIVIDER_Y))

        for i in range(self.max_visible):
            idx = self.scroll_offset + i
            if idx >= len(songs):
                break

            song = songs[idx]
            y = list_top + i * self.item_height

            # 項目背景
            item_rect = pygame.Rect(22, y + 2, SCREEN_SIZE - 44, self.item_height - 4)
            pygame.draw.rect(surface, DARK_GRAY, item_rect, border_radius=5)

            # 番号
            num = len(songs) - idx
            num_text = self.font_small.render(f"#{num}", True, GRAY)
            surface.blit(num_text, (28, y + 6))

            # 曲名
            title_str = song["title"]
            if len(title_str) > 13:
                title_str = title_str[:12] + "…"
            song_title = self.font_item.render(title_str, True, TITLE_COLOR)
            surface.blit(song_title, (50, y + 4))

            # アーティスト名
            artist_str = song["artist"]
            if len(artist_str) > 15:
                artist_str = artist_str[:14] + "…"
            artist = self.font_small.render(artist_str, True, ARTIST_COLOR)
            surface.blit(artist, (50, y + 19))

        surface.set_clip(old_clip)

        # スクロールバー（右端）
        total = len(songs)
        if total > self.max_visible:
            self._draw_scrollbar(surface, total, list_top, list_bottom)

    def _draw_scrollbar(self, surface, total, top, bottom):
        """スクロールバーを描画"""
        bar_h = bottom - top
        bar_x = SCREEN_SIZE - 16
        pygame.draw.line(surface, DARK_GRAY, (bar_x, top), (bar_x, bottom), 2)

        thumb_h = max(10, int(bar_h * self.max_visible / total))
        max_offset = total - self.max_visible
        if max_offset > 0:
            thumb_y = top + int((bar_h - thumb_h) * self.scroll_offset / max_offset)
        else:
            thumb_y = top
        pygame.draw.rect(surface, ACCENT_COLOR, (bar_x - 2, thumb_y, 6, thumb_h), border_radius=3)
