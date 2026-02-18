"""ParyboTchi - メインUI画面（キャラクター表示・録音・結果表示）"""

import math
import pygame

from config import (
    SCREEN_SIZE, SCREEN_CENTER, BG_COLOR, WHITE, BLACK, GRAY, DARK_GRAY,
    ACCENT_COLOR, LISTENING_COLOR, TEXT_COLOR, TITLE_COLOR, ARTIST_COLOR,
    RECORD_SECONDS,
)
from fonts import find_jp_font


class MainScreen:
    """メイン画面：キャラクター + ステータス + 結果表示"""

    def __init__(self):
        font_path = find_jp_font()
        self.font_large = pygame.font.Font(font_path, 18)
        self.font_medium = pygame.font.Font(font_path, 14)
        self.font_small = pygame.font.Font(font_path, 11)
        self.result_display_timer = 0
        self.result_data = None
        self.is_duplicate = False
        self.recording_progress = 0  # 0.0 ~ 1.0
        self.show_result_duration = 5.0  # 結果を表示する秒数

    def show_result(self, title, artist, is_duplicate=False):
        """認識結果を表示する"""
        self.result_data = {"title": title, "artist": artist}
        self.is_duplicate = is_duplicate
        self.result_display_timer = self.show_result_duration

    def update(self, dt):
        """タイマー更新"""
        if self.result_display_timer > 0:
            self.result_display_timer -= dt

    def draw(self, surface, character, collection, audio):
        """メイン画面を描画"""
        # 円形マスク用の背景
        surface.fill(BLACK)
        pygame.draw.circle(surface, BG_COLOR, (SCREEN_CENTER, SCREEN_CENTER), SCREEN_CENTER)

        stage = collection.get_growth_stage()

        # キャラクター描画
        character.draw(surface, stage["name"])

        # 上部：ステータス表示
        self._draw_status(surface, collection, stage)

        # 録音中のプログレスバー
        if audio.is_recording:
            self._draw_recording_indicator(surface)
        elif audio.is_analyzing:
            self._draw_analyzing_indicator(surface)
        elif self.result_display_timer > 0 and self.result_data:
            self._draw_result(surface)
        elif audio.error and not audio.is_busy:
            self._draw_error(surface, audio.error)
        else:
            # 下部：操作ヒント
            self._draw_hint(surface)

    def _draw_status(self, surface, collection, stage):
        """上部のステータス情報"""
        # 成長段階
        stage_text = self.font_small.render(
            f"{stage['name']}", True, ACCENT_COLOR,
        )
        stage_rect = stage_text.get_rect(centerx=SCREEN_CENTER, top=20)
        surface.blit(stage_text, stage_rect)

        # 曲数
        count_text = self.font_small.render(
            f"{collection.count}曲", True, GRAY,
        )
        count_rect = count_text.get_rect(centerx=SCREEN_CENTER, top=35)
        surface.blit(count_text, count_rect)

    def _draw_recording_indicator(self, surface):
        """録音中の表示"""
        # 録音テキスト
        text = self.font_medium.render("♪ きいてるよ... ♪", True, LISTENING_COLOR)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

        # プログレスバー
        bar_w = 120
        bar_h = 6
        bar_x = SCREEN_CENTER - bar_w // 2
        bar_y = SCREEN_SIZE - 42
        pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * self.recording_progress)
        if fill_w > 0:
            pygame.draw.rect(
                surface, LISTENING_COLOR,
                (bar_x, bar_y, fill_w, bar_h),
                border_radius=3,
            )

    def _draw_analyzing_indicator(self, surface):
        """解析中の表示"""
        text = self.font_medium.render("しらべてるよ...", True, ACCENT_COLOR)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

    def _draw_result(self, surface):
        """認識結果の表示"""
        data = self.result_data

        if self.is_duplicate:
            label = self.font_small.render("もう持ってるよ！", True, GRAY)
        else:
            label = self.font_small.render("みつけたよ！", True, LISTENING_COLOR)
        label_rect = label.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 75)
        surface.blit(label, label_rect)

        # 曲名（長い場合は省略）
        title_str = data["title"]
        if len(title_str) > 12:
            title_str = title_str[:11] + "…"
        title_text = self.font_medium.render(title_str, True, TITLE_COLOR)
        title_rect = title_text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 55)
        surface.blit(title_text, title_rect)

        # アーティスト名
        artist_str = data["artist"]
        if len(artist_str) > 14:
            artist_str = artist_str[:13] + "…"
        artist_text = self.font_small.render(artist_str, True, ARTIST_COLOR)
        artist_rect = artist_text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 38)
        surface.blit(artist_text, artist_rect)

    def _draw_error(self, surface, error):
        """エラー表示"""
        text = self.font_small.render(error, True, (255, 100, 100))
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

    def _draw_hint(self, surface):
        """操作ヒント"""
        text = self.font_small.render("Aボタン：きく  Bボタン：図鑑", True, GRAY)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 30)
        surface.blit(text, rect)
