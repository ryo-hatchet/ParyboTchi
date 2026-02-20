"""ParyboTchi - メインUI画面（キャラクター表示・録音・結果表示）"""

import math
import pygame

from config import (
    SCREEN_SIZE, SCREEN_CENTER, BG_COLOR, WHITE, BLACK, GRAY, DARK_GRAY,
    ACCENT_COLOR, LISTENING_COLOR, TEXT_COLOR, TITLE_COLOR, ARTIST_COLOR,
    RECORD_SECONDS,
)
from fonts import find_jp_font


# スクロール設定
_SCROLL_SPEED = 45       # ピクセル/秒
_SCROLL_THRESHOLD = 190  # テキスト幅がこれを超えたらスクロール開始
_SCROLL_PAUSE = 1.5      # 端に達したら一時停止する秒数


class MainScreen:
    """メイン画面：キャラクター + ステータス + 結果表示"""

    def __init__(self):
        font_path = find_jp_font()
        self.font_large  = pygame.font.Font(font_path, 22)   # 曲名
        self.font_medium = pygame.font.Font(font_path, 16)   # アーティスト名
        self.font_small  = pygame.font.Font(font_path, 11)   # ラベル・ヒント
        self.font_status = pygame.font.Font(font_path, 11)   # ステータス
        self.result_display_timer = 0
        self.result_data = None
        self.is_duplicate = False
        self.recording_progress = 0.0
        self.show_result_duration = 8.0  # 結果を表示する秒数

        # スクロール状態
        self._title_x   = float(SCREEN_CENTER)  # 曲名のX座標（中央スタート）
        self._artist_x  = float(SCREEN_CENTER)  # アーティストのX座標
        self._title_w   = 0    # 曲名テキスト幅
        self._artist_w  = 0    # アーティストテキスト幅
        self._title_scrolling  = False
        self._artist_scrolling = False
        self._pause_timer = 0.0  # 一時停止タイマー

    def show_result(self, title, artist, is_duplicate=False):
        """認識結果を表示する"""
        self.result_data = {"title": title, "artist": artist}
        self.is_duplicate = is_duplicate
        self.result_display_timer = self.show_result_duration
        # スクロール位置をリセット
        self._reset_scroll(title, artist)

    def _reset_scroll(self, title, artist):
        """スクロール状態を初期化"""
        title_surf  = self.font_large.render(title, True, WHITE)
        artist_surf = self.font_medium.render(artist, True, WHITE)
        self._title_w  = title_surf.get_width()
        self._artist_w = artist_surf.get_width()
        self._title_scrolling  = self._title_w  > _SCROLL_THRESHOLD
        self._artist_scrolling = self._artist_w > _SCROLL_THRESHOLD
        # スクロールするものは右端スタート、しないものは中央
        self._title_x  = float(SCREEN_SIZE + 10) if self._title_scrolling  else float(SCREEN_CENTER)
        self._artist_x = float(SCREEN_SIZE + 10) if self._artist_scrolling else float(SCREEN_CENTER)
        self._pause_timer = 0.0

    def update(self, dt):
        """タイマーとスクロール更新"""
        if self.result_display_timer > 0:
            self.result_display_timer -= dt

        if self.result_display_timer > 0 and self.result_data:
            self._update_scroll(dt)

    def _update_scroll(self, dt):
        """スクロールX座標を更新"""
        if self._pause_timer > 0:
            self._pause_timer -= dt
            return

        def advance(x, text_w, scrolling):
            if not scrolling:
                return x
            x -= _SCROLL_SPEED * dt
            # テキストが完全に左端を超えたら右端に戻す
            if x + text_w < 0:
                return float(SCREEN_SIZE + 10)
            return x

        self._title_x  = advance(self._title_x,  self._title_w,  self._title_scrolling)
        self._artist_x = advance(self._artist_x, self._artist_w, self._artist_scrolling)

    def draw(self, surface, character, collection, audio):
        """メイン画面を描画"""
        surface.fill(BLACK)
        pygame.draw.circle(surface, BG_COLOR, (SCREEN_CENTER, SCREEN_CENTER), SCREEN_CENTER)

        stage = collection.get_growth_stage()

        # キャラクター描画
        character.draw(surface, stage["name"])

        # 上部：ステータス表示
        self._draw_status(surface, collection, stage)

        # 録音中・解析中・結果・エラーの順で下部を切り替え
        if audio.is_recording:
            self._draw_recording_indicator(surface)
        elif audio.is_analyzing:
            self._draw_analyzing_indicator(surface)
        elif self.result_display_timer > 0 and self.result_data:
            self._draw_result(surface)
        elif audio.error and not audio.is_busy:
            self._draw_error(surface, audio.error)
        else:
            self._draw_hint(surface)

    def _draw_status(self, surface, collection, stage):
        """上部のステータス情報"""
        stage_text = self.font_status.render(f"{stage['name']}", True, ACCENT_COLOR)
        stage_rect = stage_text.get_rect(centerx=SCREEN_CENTER, top=20)
        surface.blit(stage_text, stage_rect)

        count_text = self.font_status.render(f"{collection.count}曲", True, GRAY)
        count_rect = count_text.get_rect(centerx=SCREEN_CENTER, top=35)
        surface.blit(count_text, count_rect)

    def _draw_recording_indicator(self, surface):
        """録音中の表示"""
        text = self.font_small.render("♪ きいてるよ... ♪", True, LISTENING_COLOR)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

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
        text = self.font_small.render("しらべてるよ...", True, ACCENT_COLOR)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

    def _draw_result(self, surface):
        """認識結果を大きく中央に表示（長い場合は右→左スクロール）"""
        data = self.result_data

        # ラベル（みつけたよ！/ もう持ってるよ！）
        if self.is_duplicate:
            label = self.font_small.render("もう持ってるよ！", True, GRAY)
        else:
            label = self.font_small.render("みつけたよ！", True, LISTENING_COLOR)
        label_rect = label.get_rect(centerx=SCREEN_CENTER, top=62)
        surface.blit(label, label_rect)

        # クリッピング領域（テキストが円形画面の外に出ないように）
        clip_rect = pygame.Rect(10, 80, SCREEN_SIZE - 20, 100)
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        # 曲名（大きく表示）
        title_surf = self.font_large.render(data["title"], True, TITLE_COLOR)
        if self._title_scrolling:
            surface.blit(title_surf, (int(self._title_x), 88))
        else:
            title_rect = title_surf.get_rect(centerx=SCREEN_CENTER, top=88)
            surface.blit(title_surf, title_rect)

        # アーティスト名
        artist_surf = self.font_medium.render(data["artist"], True, ARTIST_COLOR)
        if self._artist_scrolling:
            surface.blit(artist_surf, (int(self._artist_x), 120))
        else:
            artist_rect = artist_surf.get_rect(centerx=SCREEN_CENTER, top=120)
            surface.blit(artist_surf, artist_rect)

        surface.set_clip(old_clip)

    def _draw_error(self, surface, error):
        """エラー表示"""
        text = self.font_small.render(error, True, (255, 100, 100))
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

    def _draw_hint(self, surface):
        """操作ヒント"""
        text = self.font_small.render("タップ：きく  左スワイプ：図鑑", True, GRAY)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 28)
        surface.blit(text, rect)
