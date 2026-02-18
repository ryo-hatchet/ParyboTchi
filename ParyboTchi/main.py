"""ParyboTchi - メインアプリケーション

音楽を集めて育てる「たまごっち」風キャラクター

操作方法 (PC):
  Z キー: ボタンA (録音開始 / アーカイブでスクロール)
  X キー: ボタンB (画面切り替え)
  ESC: 終了
"""

import time
import pygame

from config import SCREEN_SIZE, FPS, BG_COLOR, BLACK, IS_RASPBERRY_PI, RECORD_SECONDS
from audio import AudioRecognizer
from data import SongCollection
from character import Character
from ui_main import MainScreen
from ui_archive import ArchiveScreen
from hardware import InputHandler


class App:
    """ParyboTchi メインアプリケーション"""

    # 画面状態
    SCREEN_MAIN = 0
    SCREEN_ARCHIVE = 1

    def __init__(self):
        pygame.init()

        if IS_RASPBERRY_PI:
            self.screen = pygame.display.set_mode(
                (SCREEN_SIZE, SCREEN_SIZE), pygame.FULLSCREEN,
            )
            pygame.mouse.set_visible(False)
        else:
            self.screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
            pygame.display.set_caption("ParyboTchi")

        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = self.SCREEN_MAIN

        # モジュール初期化
        self.audio = AudioRecognizer()
        self.collection = SongCollection()
        self.character = Character()
        self.main_ui = MainScreen()
        self.archive_ui = ArchiveScreen()
        self.input = InputHandler()

        # 録音の進捗計測用
        self._record_start_time = 0

    def run(self):
        """メインループ"""
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0
                events = pygame.event.get()
                self._handle_events(events, dt)
                self._update(dt)
                self._draw()
                pygame.display.flip()
        finally:
            self.input.cleanup()
            pygame.quit()

    def _handle_events(self, events, dt):
        """イベント処理"""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            elif event.type == pygame.USEREVENT + 1:
                self.character.emotion = "normal"

        self.input.update(events)

        if self.current_screen == self.SCREEN_MAIN:
            self._handle_main_input()
        elif self.current_screen == self.SCREEN_ARCHIVE:
            self._handle_archive_input()

    def _handle_main_input(self):
        """メイン画面の入力処理"""
        # ボタンA: 録音開始
        if self.input.button_a_pressed and not self.audio.is_busy:
            self.audio.start_recognition()
            self._record_start_time = time.time()
            self.character.emotion = "listening"
            self.main_ui.result_display_timer = 0
            self.audio.error = None

        # ボタンB: アーカイブ画面へ
        if self.input.button_b_pressed and not self.audio.is_busy:
            self.current_screen = self.SCREEN_ARCHIVE
            self.archive_ui.reset_scroll()

    def _handle_archive_input(self):
        """アーカイブ画面の入力処理"""
        # ボタンA: スクロール
        if self.input.button_a_pressed:
            self.archive_ui.scroll_down(self.collection.count)

        # ボタンB: メイン画面へ戻る
        if self.input.button_b_pressed:
            self.current_screen = self.SCREEN_MAIN

    def _update(self, dt):
        """状態更新"""
        self.character.update(dt)
        self.main_ui.update(dt)

        # 録音中のプログレス更新
        if self.audio.is_recording:
            elapsed = time.time() - self._record_start_time
            self.main_ui.recording_progress = min(elapsed / RECORD_SECONDS, 1.0)

        # 認識完了チェック
        if not self.audio.is_busy and self.character.emotion == "listening":
            if self.audio.result:
                title = self.audio.result["title"]
                artist = self.audio.result["artist"]
                is_new = self.collection.add_song(title, artist)
                self.main_ui.show_result(title, artist, is_duplicate=not is_new)
                self.character.emotion = "happy"
                # 3秒後にnormalに戻すタイマー（簡易）
                pygame.time.set_timer(pygame.USEREVENT + 1, 3000, loops=1)
            else:
                self.character.emotion = "normal"

        # 解析中は表示更新
        if self.audio.is_analyzing:
            self.main_ui.recording_progress = 1.0

    def _draw(self):
        """画面描画"""
        if self.current_screen == self.SCREEN_MAIN:
            self.main_ui.draw(self.screen, self.character, self.collection, self.audio)
        elif self.current_screen == self.SCREEN_ARCHIVE:
            self.archive_ui.draw(self.screen, self.collection)


if __name__ == "__main__":
    app = App()
    app.run()
