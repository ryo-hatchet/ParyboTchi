"""ParyboTchi - 曲解説画面UI"""

import pygame

from config import (
    SCREEN_SIZE, SCREEN_CENTER, BLACK, BG_COLOR, WHITE, GRAY,
    ACCENT_COLOR, DARK_GRAY, DESCRIPTION_DISPLAY_SECONDS,
)
from fonts import find_jp_font


class DescriptionScreen:
    """曲の解説を表示する画面"""

    def __init__(self):
        font_path = find_jp_font()
        self.font_title = pygame.font.Font(font_path, 14)
        self.font_artist = pygame.font.Font(font_path, 11)
        self.font_body = pygame.font.Font(font_path, 14)
        self.font_label = pygame.font.Font(font_path, 11)

        self.title = ""
        self.artist = ""
        self.description = ""
        self.display_timer = 0.0
        self._wrapped_lines = []
        self._loading = False

    def show(self, title, artist, description=None):
        """解説画面を表示する"""
        self.title = title
        self.artist = artist
        if description:
            self.description = description
            self._wrapped_lines = self._wrap_text(description, self.font_body, 170)
            self._loading = False
        else:
            self.description = ""
            self._wrapped_lines = []
            self._loading = True
        self.display_timer = DESCRIPTION_DISPLAY_SECONDS

    def set_description(self, description):
        """解説テキストを後から設定する（API応答後）"""
        self.description = description
        self._wrapped_lines = self._wrap_text(description, self.font_body, 170)
        self._loading = False
        # テキスト設定時にタイマーをリセット
        self.display_timer = DESCRIPTION_DISPLAY_SECONDS

    def update(self, dt):
        """タイマー更新"""
        if self._loading:
            return  # ローディング中はタイマーを進めない
        if self.display_timer > 0:
            self.display_timer -= dt
            if self.display_timer <= 0:
                self.display_timer = 0

    @property
    def is_finished(self):
        """表示が終了したか"""
        return not self._loading and self.display_timer <= 0

    def _wrap_text(self, text, font, max_width):
        """テキストを指定幅で折り返す"""
        lines = []
        current_line = ""
        for char in text:
            if char == "\n":
                lines.append(current_line)
                current_line = ""
                continue
            test_line = current_line + char
            if font.size(test_line)[0] > max_width:
                lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
        return lines

    def draw(self, surface):
        """解説画面を描画"""
        surface.fill(BLACK)
        pygame.draw.circle(surface, BG_COLOR, (SCREEN_CENTER, SCREEN_CENTER), SCREEN_CENTER)

        # 上部: 曲情報
        y = 35
        title_surf = self.font_title.render(self.title, True, ACCENT_COLOR)
        title_rect = title_surf.get_rect(centerx=SCREEN_CENTER, top=y)
        # 曲名が長い場合はクリッピング
        if title_surf.get_width() > 180:
            truncated = self._truncate_text(self.title, self.font_title, 170)
            title_surf = self.font_title.render(truncated, True, ACCENT_COLOR)
            title_rect = title_surf.get_rect(centerx=SCREEN_CENTER, top=y)
        surface.blit(title_surf, title_rect)

        y += 18
        artist_surf = self.font_artist.render(self.artist, True, GRAY)
        artist_rect = artist_surf.get_rect(centerx=SCREEN_CENTER, top=y)
        surface.blit(artist_surf, artist_rect)

        # 区切り線
        y += 18
        pygame.draw.line(surface, DARK_GRAY, (50, y), (190, y), 1)

        # 本文エリア
        y += 8
        if self._loading:
            # ローディング表示
            loading_surf = self.font_label.render("しらべてるよ...", True, GRAY)
            loading_rect = loading_surf.get_rect(centerx=SCREEN_CENTER, centery=150)
            surface.blit(loading_surf, loading_rect)
        else:
            # 解説テキスト表示
            for line in self._wrapped_lines:
                line_surf = self.font_body.render(line, True, WHITE)
                line_rect = line_surf.get_rect(centerx=SCREEN_CENTER, top=y)
                surface.blit(line_surf, line_rect)
                y += 19

        # 下部: ヒント
        hint_surf = self.font_label.render("タップで戻る", True, DARK_GRAY)
        hint_rect = hint_surf.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 25)
        surface.blit(hint_surf, hint_rect)

    def _truncate_text(self, text, font, max_width):
        """テキストを指定幅に収まるよう省略する"""
        for i in range(len(text), 0, -1):
            truncated = text[:i] + "..."
            if font.size(truncated)[0] <= max_width:
                return truncated
        return "..."
