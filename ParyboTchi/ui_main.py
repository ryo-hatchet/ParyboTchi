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
_SCROLL_SPEED = 45       # ピクセル/秒
_SCROLL_THRESHOLD = 160  # テキスト幅がこれを超えたらスクロール開始（26pxフォント対応）
_SCROLL_PAUSE = 1.5      # 端に達したら一時停止する秒数


class MainScreen:
    """メイン画面：キャラクター + ステータス + 結果表示"""

    def __init__(self):
        font_path = find_jp_font()
        self.font_large  = pygame.font.Font(font_path, 28)   # 曲名（拡大）
        self.font_medium = pygame.font.Font(font_path, 20)   # アーティスト名（拡大）
        self.font_small  = pygame.font.Font(font_path, 13)   # ラベル・ヒント
        self.font_status = pygame.font.Font(font_path, 13)   # ステータス
        self.result_display_timer = 0
        self.result_data = None
        self.is_duplicate = False
        self.recording_progress = 0.0
        self.show_result_duration = 5.0  # 結果を表示する秒数

        # スクロール状態
        self._title_x   = float(SCREEN_CENTER)  # 曲名のX座標（中央スタート）
        self._artist_x  = float(SCREEN_CENTER)  # アーティストのX座標
        self._title_w   = 0    # 曲名テキスト幅
        self._artist_w  = 0    # アーティストテキスト幅
        self._title_scrolling  = False
        self._artist_scrolling = False
        self._pause_timer = 0.0  # 一時停止タイマー

        # 音符アニメーション
        self.note_timer = 0.0
        NOTE_CHARS = ["♩", "♪", "♫", "♬"]
        self._note_surfs = [self.font_small.render(c, True, NOTE_COLOR) for c in NOTE_CHARS]

        # キラキラエフェクト
        self.sparkle_timer = 0.0
        self.sparkle_duration = 3.0
        self._sparkles = []

    def show_result(self, title, artist, is_duplicate=False):
        """認識結果を表示する"""
        self.result_data = {"title": title, "artist": artist}
        self.is_duplicate = is_duplicate
        self.result_display_timer = self.show_result_duration
        # スクロール・キラキラをリセット
        self._reset_scroll(title, artist)
        self.sparkle_timer = 0.0
        self._sparkles = []

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
            self.sparkle_timer += dt
            self._update_sparkles(dt)

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

    def _update_sparkles(self, dt):
        """キラキラパーティクルの更新"""
        # 生成（duration内のみ）: 毎フレーム5個生成（2個×2.5倍）
        if self.sparkle_timer < self.sparkle_duration:
            for _ in range(5):
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(20, 85)
                x = SCREEN_CENTER + int(math.cos(angle) * dist)
                y = SCREEN_CENTER + int(math.sin(angle) * dist)
                max_life = random.uniform(0.3, 0.8)
                colors = [
                    (255, 220, 100),  # 金
                    (255, 150, 200),  # ピンク
                    (150, 220, 255),  # 水色
                    (200, 255, 150),  # 黄緑
                ]
                self._sparkles.append({
                    "x": x, "y": y,
                    "size": random.randint(4, 12),  # 2〜5 → 4〜12（約2.5倍）
                    "life": max_life,
                    "max_life": max_life,
                    "color": random.choice(colors),
                })

        # 更新・削除
        for s in self._sparkles:
            s["life"] -= dt
        self._sparkles = [s for s in self._sparkles if s["life"] > 0]

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
            if self.sparkle_timer < self.sparkle_duration:
                self._draw_sparkle(surface)
        elif audio.is_recording:
            self._draw_recording_indicator(surface)
        elif audio.is_analyzing:
            self._draw_analyzing_indicator(surface)
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

        # 音符アニメーション（sin波で上下・フェード）
        for i, note_surf in enumerate(self._note_surfs):
            phase = (i / 4) * 2 * math.pi
            x = SCREEN_CENTER + int(math.sin(self.note_timer * 1.2 + phase) * 35)
            y = 100 + i * 12 + int(math.sin(self.note_timer * 2.0 + phase * 1.5) * 6)
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

    def _draw_sparkle(self, surface):
        """キラキラエフェクトを描画（軽量: draw.circle使用）"""
        for s in self._sparkles:
            brightness = s["life"] / s["max_life"]
            color = tuple(int(c * brightness) for c in s["color"])
            pygame.draw.circle(surface, color, (s["x"], s["y"]), s["size"])

    def _draw_error(self, surface, error):
        """エラー表示"""
        text = self.font_small.render(error, True, (255, 100, 100))
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 50)
        surface.blit(text, rect)

    def _draw_hint(self, surface):
        """操作ヒント"""
        text = self.font_small.render("長押し：きく  左スワイプ：図鑑", True, GRAY)
        rect = text.get_rect(centerx=SCREEN_CENTER, bottom=SCREEN_SIZE - 28)
        surface.blit(text, rect)
