"""ParyboTchi - メインUI画面（キャラクター表示・録音・結果表示）"""

import math
import random
import pygame

from config import (
    SCREEN_SIZE, SCREEN_CENTER, BG_COLOR, WHITE, BLACK, GRAY, DARK_GRAY,
    ACCENT_COLOR, LISTENING_COLOR, TEXT_COLOR, TITLE_COLOR, ARTIST_COLOR,
    NOTE_COLOR, HAPPY_COLOR,
    RECORD_SECONDS,
)
from fonts import find_jp_font


# スクロール設定
_SCROLL_SPEED = 54       # ピクセル/秒（45 × 1.2）
_SCROLL_THRESHOLD = 160  # テキスト幅がこれを超えたらスクロール開始（28pxフォント対応）
_SCROLL_PAUSE = 1.5      # 端に達したら一時停止する秒数


class MainScreen:
    """メイン画面：キャラクター + ステータス + 結果表示"""

    def __init__(self):
        font_path = find_jp_font()
        self.font_large  = pygame.font.Font(font_path, 28)   # 曲名
        self.font_medium = pygame.font.Font(font_path, 20)   # アーティスト名
        self.font_small  = pygame.font.Font(font_path, 13)   # ラベル
        self.font_status = pygame.font.Font(font_path, 13)   # ステータス
        self.font_note   = pygame.font.Font(font_path, 26)   # 音符（2倍: 13→26）
        self.font_levelup = pygame.font.Font(font_path, 22)  # レベルアップ大テキスト
        self.font_levelup_sub = pygame.font.Font(font_path, 15)  # レベルアップサブ
        self.result_display_timer = 0
        self.result_data = None
        self.is_duplicate = False
        self.recording_progress = 0.0
        self.show_result_duration = 15.0  # 結果を表示する秒数

        # スクロール状態
        self._title_x   = float(SCREEN_CENTER)  # 曲名のX座標（中央スタート）
        self._artist_x  = float(SCREEN_CENTER)  # アーティストのX座標
        self._title_w   = 0    # 曲名テキスト幅
        self._artist_w  = 0    # アーティストテキスト幅
        self._title_scrolling  = False
        self._artist_scrolling = False
        self._pause_timer = 0.0  # 一時停止タイマー

        # 音符アニメーション（2倍サイズ font_note で事前レンダリング）
        self.note_timer = 0.0
        NOTE_CHARS = ["♩", "♪", "♫", "♬"]
        self._note_surfs = [self.font_note.render(c, True, NOTE_COLOR) for c in NOTE_CHARS]

        # レベルアップ演出
        self.levelup_timer = 0.0
        self.levelup_duration = 4.0
        self.levelup_stage_name = ""

    def show_result(self, title, artist, is_duplicate=False):
        """認識結果を表示する"""
        self.result_data = {"title": title, "artist": artist}
        self.is_duplicate = is_duplicate
        self.result_display_timer = self.show_result_duration
        # スクロールをリセット
        self._reset_scroll(title, artist)

    def show_levelup(self, stage_name):
        """レベルアップ演出を開始する"""
        self.levelup_stage_name = stage_name
        self.levelup_timer = self.levelup_duration

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
        self.note_timer += dt

        if self.result_display_timer > 0:
            self.result_display_timer -= dt
            # タイマーが0になったら結果表示を自動クリア
            if self.result_display_timer <= 0:
                self.result_data = None
                self.result_display_timer = 0

        if self.result_display_timer > 0 and self.result_data:
            self._update_scroll(dt)

        if self.levelup_timer > 0:
            self.levelup_timer -= dt

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

        # 結果表示中はキャラクターを半透明で描画
        char_alpha = 128 if (self.result_display_timer > 0 and self.result_data) else 255
        character.draw(surface, stage["name"], alpha=char_alpha)

        # 上部：ステータス表示
        self._draw_status(surface, collection, stage)

        # 録音中・解析中・結果・エラーの順で下部を切り替え
        # ※ 結果表示タイマーを最優先（is_analyzingより先にチェック）
        if self.result_display_timer > 0 and self.result_data:
            self._draw_result(surface)
        elif audio.is_recording:
            self._draw_recording_indicator(surface)
        elif audio.is_analyzing:
            self._draw_analyzing_indicator(surface)
        elif audio.error and not audio.is_busy:
            self._draw_error(surface, audio.error)

        # レベルアップ演出（最前面に重ねる）
        if self.levelup_timer > 0:
            self._draw_levelup(surface)

    def _draw_status(self, surface, collection, stage):
        """上部のステータス情報"""
        stage_text = self.font_status.render(f"{stage['name']}", True, ACCENT_COLOR)
        stage_rect = stage_text.get_rect(centerx=SCREEN_CENTER, top=20)
        surface.blit(stage_text, stage_rect)

        count_text = self.font_status.render(f"{collection.count}曲", True, GRAY)
        count_rect = count_text.get_rect(centerx=SCREEN_CENTER, top=35)
        surface.blit(count_text, count_rect)

    def _draw_recording_indicator(self, surface):
        """録音中の表示（音符アニメーション付き）"""
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

        # 音符アニメーション（sin波で上下・フェード・2倍サイズ）
        for i, note_surf in enumerate(self._note_surfs):
            phase = (i / 4) * 2 * math.pi
            x = SCREEN_CENTER + int(math.sin(self.note_timer * 1.2 + phase) * 35)
            y = 105 + i * 16 + int(math.sin(self.note_timer * 2.0 + phase * 1.5) * 6)
            alpha = int((math.sin(self.note_timer * 1.5 + phase) + 1) / 2 * 220) + 35
            tmp = note_surf.copy()
            tmp.set_alpha(max(35, min(255, alpha)))
            surface.blit(tmp, tmp.get_rect(centerx=x, centery=y))

    def _draw_analyzing_indicator(self, surface):
        """解析中の表示"""
        text = self.font_small.render("しらべてるよ...", True, ACCENT_COLOR)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

    def _draw_result(self, surface):
        """認識結果を全面に表示（キャラクターより前面）"""
        data = self.result_data

        # 全画面半透明黒オーバーレイ（キャラクターを完全に覆う）
        overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # ラベル（みつけたよ！/ もう持ってるよ！）
        if self.is_duplicate:
            label = self.font_small.render("もう持ってるよ！", True, GRAY)
        else:
            label = self.font_small.render("みつけたよ！", True, LISTENING_COLOR)
        label_rect = label.get_rect(centerx=SCREEN_CENTER, centery=75)
        surface.blit(label, label_rect)

        # 曲名（中央に大きく表示・クリッピングなし）
        title_surf = self.font_large.render(data["title"], True, TITLE_COLOR)
        if self._title_scrolling:
            surface.blit(title_surf, (int(self._title_x), 100))
        else:
            title_rect = title_surf.get_rect(centerx=SCREEN_CENTER, centery=110)
            surface.blit(title_surf, title_rect)

        # アーティスト名
        artist_surf = self.font_medium.render(data["artist"], True, ARTIST_COLOR)
        if self._artist_scrolling:
            surface.blit(artist_surf, (int(self._artist_x), 145))
        else:
            artist_rect = artist_surf.get_rect(centerx=SCREEN_CENTER, centery=148)
            surface.blit(artist_surf, artist_rect)

    def _draw_levelup(self, surface):
        """レベルアップ演出（フルスクリーンオーバーレイ）"""
        # フェードイン・アウト計算
        progress = self.levelup_timer / self.levelup_duration
        # 前半はフェードイン、後半はフェードアウト
        if progress > 0.7:
            fade = (1.0 - progress) / 0.3  # 後半0.3でフェードアウト → 0→1
            alpha = int(fade * 210)
        elif progress > 0.5:
            alpha = 210
        else:
            alpha = int(progress / 0.5 * 210)  # 前半0.5でフェードイン

        # 半透明紫オーバーレイ
        overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE), pygame.SRCALPHA)
        overlay.fill((80, 20, 140, alpha))
        surface.blit(overlay, (0, 0))

        text_alpha = min(255, int(alpha * 1.2))

        # "LEVEL UP!" テキスト
        lu_surf = self.font_levelup.render("LEVEL  UP !", True, (255, 240, 80))
        lu_surf.set_alpha(text_alpha)
        surface.blit(lu_surf, lu_surf.get_rect(centerx=SCREEN_CENTER, centery=100))

        # ステージ名
        stage_surf = self.font_levelup_sub.render(self.levelup_stage_name, True, WHITE)
        stage_surf.set_alpha(text_alpha)
        surface.blit(stage_surf, stage_surf.get_rect(centerx=SCREEN_CENTER, centery=135))

        # 星マーク装飾
        stars = ["★", "☆", "★"]
        star_surf = self.font_levelup_sub.render("  ".join(stars), True, (255, 220, 60))
        star_surf.set_alpha(text_alpha)
        surface.blit(star_surf, star_surf.get_rect(centerx=SCREEN_CENTER, centery=160))

    def _draw_error(self, surface, error):
        """エラー表示"""
        text = self.font_small.render(error, True, (255, 100, 100))
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)
