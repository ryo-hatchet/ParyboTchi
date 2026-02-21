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
from config import SPI_PORT, SPI_CS, SPI_DC, SPI_RST, SPI_BL, SPI_SPEED
from audio import AudioRecognizer
from data import SongCollection
from character import Character
from ui_main import MainScreen
from ui_archive import ArchiveScreen
from hardware import InputHandler

# Waveshare GC9A01 ディスプレイドライバー
LCD = None
if IS_RASPBERRY_PI:
    try:
        import spidev
        import RPi.GPIO as GPIO
        from PIL import Image

        class GC9A01:
            """Waveshare 1.28inch Round LCD (GC9A01) SPIドライバー"""

            def __init__(self, dc, rst, bl, spi_port=0, spi_cs=0, spi_speed=40000000):
                self.dc = dc
                self.rst = rst
                self.bl = bl

                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.dc, GPIO.OUT)
                GPIO.setup(self.rst, GPIO.OUT)
                GPIO.setup(self.bl, GPIO.OUT)

                self.spi = spidev.SpiDev()
                self.spi.open(spi_port, spi_cs)
                self.spi.max_speed_hz = spi_speed
                self.spi.mode = 0

                self._init_display()
                GPIO.output(self.bl, GPIO.HIGH)  # バックライトON

            def _cmd(self, cmd):
                GPIO.output(self.dc, GPIO.LOW)
                self.spi.writebytes([cmd])

            def _data(self, data):
                GPIO.output(self.dc, GPIO.HIGH)
                if isinstance(data, int):
                    self.spi.writebytes([data])
                else:
                    # 4096バイトずつ分割して送信
                    for i in range(0, len(data), 4096):
                        self.spi.writebytes(data[i:i + 4096])

            def _reset(self):
                GPIO.output(self.rst, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(self.rst, GPIO.LOW)
                time.sleep(0.1)
                GPIO.output(self.rst, GPIO.HIGH)
                time.sleep(0.1)

            def _init_display(self):
                self._reset()
                self._cmd(0xEF)
                self._cmd(0xEB); self._data(0x14)
                self._cmd(0xFE)
                self._cmd(0xEF)
                self._cmd(0xEB); self._data(0x14)
                self._cmd(0x84); self._data(0x40)
                self._cmd(0x85); self._data(0xFF)
                self._cmd(0x86); self._data(0xFF)
                self._cmd(0x87); self._data(0xFF)
                self._cmd(0x88); self._data(0x0A)
                self._cmd(0x89); self._data(0x21)
                self._cmd(0x8A); self._data(0x00)
                self._cmd(0x8B); self._data(0x80)
                self._cmd(0x8C); self._data(0x01)
                self._cmd(0x8D); self._data(0x01)
                self._cmd(0x8E); self._data(0xFF)
                self._cmd(0x8F); self._data(0xFF)
                self._cmd(0xB6); self._data(0x00); self._data(0x00)
                self._cmd(0x36); self._data(0x48)  # MADCTL: MX=1(水平反転OFF), BGR=1
                self._cmd(0x3A); self._data(0x05)  # RGB565
                self._cmd(0x90); self._data(0x08); self._data(0x08); self._data(0x08); self._data(0x08)
                self._cmd(0xBD); self._data(0x06)
                self._cmd(0xBC); self._data(0x00)
                self._cmd(0xFF); self._data(0x60); self._data(0x01); self._data(0x04)
                self._cmd(0xC3); self._data(0x13)
                self._cmd(0xC4); self._data(0x13)
                self._cmd(0xC9); self._data(0x22)
                self._cmd(0xBE); self._data(0x11)
                self._cmd(0xE1); self._data(0x10); self._data(0x0E)
                self._cmd(0xDF); self._data(0x21); self._data(0x0c); self._data(0x02)
                self._cmd(0xF0); self._data(0x45); self._data(0x09); self._data(0x08); self._data(0x08); self._data(0x26); self._data(0x2A)
                self._cmd(0xF1); self._data(0x43); self._data(0x70); self._data(0x72); self._data(0x36); self._data(0x37); self._data(0x6F)
                self._cmd(0xF2); self._data(0x45); self._data(0x09); self._data(0x08); self._data(0x08); self._data(0x26); self._data(0x2A)
                self._cmd(0xF3); self._data(0x43); self._data(0x70); self._data(0x72); self._data(0x36); self._data(0x37); self._data(0x6F)
                self._cmd(0xED); self._data(0x1B); self._data(0x0B)
                self._cmd(0xAE); self._data(0x77)
                self._cmd(0xCD); self._data(0x63)
                self._cmd(0x70); self._data(0x07); self._data(0x07); self._data(0x04); self._data(0x0E); self._data(0x0F); self._data(0x09); self._data(0x07); self._data(0x08); self._data(0x03)
                self._cmd(0xE8); self._data(0x34)
                self._cmd(0x62); self._data(0x18); self._data(0x0D); self._data(0x71); self._data(0xED); self._data(0x70); self._data(0x70); self._data(0x18); self._data(0x0F); self._data(0x71); self._data(0xEF); self._data(0x70); self._data(0x70)
                self._cmd(0x63); self._data(0x18); self._data(0x11); self._data(0x71); self._data(0xF1); self._data(0x70); self._data(0x70); self._data(0x18); self._data(0x13); self._data(0x71); self._data(0xF3); self._data(0x70); self._data(0x70)
                self._cmd(0x64); self._data(0x28); self._data(0x29); self._data(0xF1); self._data(0x01); self._data(0xF1); self._data(0x00); self._data(0x07)
                self._cmd(0x66); self._data(0x3C); self._data(0x00); self._data(0xCD); self._data(0x67); self._data(0x45); self._data(0x45); self._data(0x10); self._data(0x00); self._data(0x00); self._data(0x00)
                self._cmd(0x67); self._data(0x00); self._data(0x3C); self._data(0x00); self._data(0x00); self._data(0x00); self._data(0x01); self._data(0x54); self._data(0x10); self._data(0x32); self._data(0x98)
                self._cmd(0x74); self._data(0x10); self._data(0x85); self._data(0x80); self._data(0x00); self._data(0x00); self._data(0x4E); self._data(0x00)
                self._cmd(0x98); self._data(0x3e); self._data(0x07)
                self._cmd(0x35)
                self._cmd(0x21)  # 色反転ON
                self._cmd(0x11)  # スリープ解除
                time.sleep(0.12)
                self._cmd(0x29)  # ディスプレイON
                time.sleep(0.02)

            def show(self, surface):
                """pygame Surface を BGR565 に変換してSPIで送信（GC9A01はBGR順）"""
                import numpy as np
                # 240x240 にスケール（FULLSCREEN時に実際のサイズが異なる場合に対応）
                scaled = pygame.transform.scale(surface, (SCREEN_SIZE, SCREEN_SIZE))
                raw = pygame.image.tostring(scaled, "RGB")
                arr = np.frombuffer(raw, dtype=np.uint8).reshape((SCREEN_SIZE, SCREEN_SIZE, 3))

                # MADCTL BGR=1 でHW側がBGR変換するのでソフト側はRGB順でOK
                r = arr[:, :, 0].astype(np.uint16)
                g = arr[:, :, 1].astype(np.uint16)
                b = arr[:, :, 2].astype(np.uint16)
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

                # ビッグエンディアンで並べ替え
                buf = np.zeros(SCREEN_SIZE * SCREEN_SIZE * 2, dtype=np.uint8)
                buf[0::2] = (rgb565 >> 8).flatten().astype(np.uint8)
                buf[1::2] = (rgb565 & 0xFF).flatten().astype(np.uint8)

                # 描画範囲をフルスクリーンに設定
                self._cmd(0x2A)
                self._data(0x00); self._data(0x00)
                self._data(0x00); self._data(0xEF)  # 239

                self._cmd(0x2B)
                self._data(0x00); self._data(0x00)
                self._data(0x00); self._data(0xEF)  # 239

                self._cmd(0x2C)
                self._data(buf.tolist())

            def cleanup(self):
                try:
                    GPIO.output(self.bl, GPIO.LOW)
                except Exception:
                    pass
                self.spi.close()

        LCD = GC9A01(
            dc=SPI_DC,
            rst=SPI_RST,
            bl=SPI_BL,
            spi_port=SPI_PORT,
            spi_cs=SPI_CS,
            spi_speed=SPI_SPEED,
        )
        print("Waveshare 1.28inch LCD 初期化完了")
    except Exception as e:
        print(f"LCD初期化エラー（無視して続行）: {e}")
        LCD = None


class App:
    """ParyboTchi メインアプリケーション"""

    # 画面状態
    SCREEN_MAIN = 0
    SCREEN_ARCHIVE = 1

    def __init__(self):
        pygame.init()

        if IS_RASPBERRY_PI:
            # FULLSCREENは実際の解像度になるため、描画用に240x240固定バッファを用意
            self.display = pygame.display.set_mode(
                (SCREEN_SIZE, SCREEN_SIZE), pygame.NOFRAME,
            )
            self.screen = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
            pygame.mouse.set_visible(False)
        else:
            self.display = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))
            self.screen = self.display
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
                # 描画バッファを display に転送（PC では同一オブジェクト）
                if IS_RASPBERRY_PI:
                    self.display.blit(self.screen, (0, 0))
                pygame.display.flip()

                # Waveshare LCD に転送
                if LCD:
                    LCD.show(self.screen)
        finally:
            self.input.cleanup()
            if LCD:
                LCD.cleanup()
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

    def _start_recording(self):
        """録音を開始する共通処理"""
        self.audio.start_recognition()
        self._record_start_time = time.time()
        self.character.emotion = "listening"
        self.main_ui.result_display_timer = 0
        self.audio.error = None

    def _go_to_archive(self):
        """アーカイブ画面に移動する共通処理"""
        self.current_screen = self.SCREEN_ARCHIVE
        self.archive_ui.reset_scroll()

    def _handle_main_input(self):
        """メイン画面の入力処理"""
        # ボタンA or タップ: 録音開始
        if (self.input.button_a_pressed or self.input.double_tap) and not self.audio.is_busy:
            self._start_recording()

        # ボタンB or 右スワイプ: アーカイブ画面へ
        if (self.input.button_b_pressed or self.input.swipe_right) and not self.audio.is_busy:
            self._go_to_archive()

    def _handle_archive_input(self):
        """アーカイブ画面の入力処理"""
        # 下スワイプ or ボタンA or ロングプレス: スクロール
        if self.input.swipe_down or self.input.button_a_pressed or self.input.double_tap:
            self.archive_ui.scroll_down(self.collection.count)

        # ボタンB or 左スワイプ: メイン画面へ戻る
        if self.input.button_b_pressed or self.input.swipe_left:
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
