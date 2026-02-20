"""ParyboTchi - ハードウェア入力モジュール（GPIO / タッチ / キーボード抽象化）"""

import time
import pygame
from config import IS_RASPBERRY_PI, BUTTON_A_PIN, BUTTON_B_PIN

GPIO = None
if IS_RASPBERRY_PI:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        pass

# タッチパネル設定 (CST816S I2C)
TOUCH_I2C_ADDR = 0x15
TOUCH_SDA_PIN  = 2   # I2C SDA (GPIO2)
TOUCH_SCL_PIN  = 3   # I2C SCL (GPIO3)
TOUCH_INT_PIN  = 4   # 割り込みピン (TP_INT)
TOUCH_RST_PIN  = 17  # リセットピン (TP_RST)

# タッチジェスチャーコード (CST816S)
GESTURE_NONE        = 0x00
GESTURE_SWIPE_UP    = 0x01
GESTURE_SWIPE_DOWN  = 0x02
GESTURE_SWIPE_LEFT  = 0x03
GESTURE_SWIPE_RIGHT = 0x04
GESTURE_CLICK       = 0x05
GESTURE_DOUBLE_TAP  = 0x0B


class TouchHandler:
    """CST816S タッチパネルを I2C で読み取るクラス"""

    def __init__(self):
        self.smbus = None
        self._last_tap_time = 0
        self._double_tap_threshold = 0.4  # ダブルタップ判定秒数

        if not IS_RASPBERRY_PI:
            return
        try:
            import smbus2
            # タッチコントローラーリセット
            if GPIO:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(TOUCH_RST_PIN, GPIO.OUT)
                GPIO.setup(TOUCH_INT_PIN, GPIO.IN)
                GPIO.output(TOUCH_RST_PIN, GPIO.LOW)
                time.sleep(0.05)
                GPIO.output(TOUCH_RST_PIN, GPIO.HIGH)
                time.sleep(0.1)
            self.smbus = smbus2.SMBus(1)
        except Exception as e:
            print(f"タッチパネル初期化エラー（無視）: {e}")
            self.smbus = None

    def read_gesture(self):
        """ジェスチャーコードを読み取る。読み取れない場合は GESTURE_NONE"""
        if not self.smbus:
            return GESTURE_NONE
        try:
            data = self.smbus.read_i2c_block_data(TOUCH_I2C_ADDR, 0x01, 6)
            gesture = data[0]
            return gesture
        except Exception:
            return GESTURE_NONE

    def cleanup(self):
        if self.smbus:
            self.smbus.close()


class InputHandler:
    """ボタン・タッチ入力を抽象化するクラス

    Raspberry Pi: GPIO ボタン + タッチパネル
    PC: キーボード (Z=ボタンA, X=ボタンB, C=ダブルタップ, V=右スワイプ)
    """

    def __init__(self):
        self.button_a_pressed = False   # 録音開始
        self.button_b_pressed = False   # アーカイブ表示
        self.double_tap = False         # ダブルタップ → 録音開始
        self.swipe_right = False        # 右スワイプ → アーカイブ表示
        self._prev_a = False
        self._prev_b = False

        if IS_RASPBERRY_PI and GPIO:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUTTON_A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(BUTTON_B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.touch = TouchHandler()

    def update(self, events):
        """入力状態を更新。押した瞬間だけTrueになる（エッジ検出）"""
        self.button_a_pressed = False
        self.button_b_pressed = False
        self.double_tap = False
        self.swipe_right = False

        if IS_RASPBERRY_PI and GPIO:
            # GPIO ボタン
            a = not GPIO.input(BUTTON_A_PIN)
            b = not GPIO.input(BUTTON_B_PIN)
            if a and not self._prev_a:
                self.button_a_pressed = True
            if b and not self._prev_b:
                self.button_b_pressed = True
            self._prev_a = a
            self._prev_b = b

            # タッチパネル
            gesture = self.touch.read_gesture()
            if gesture == GESTURE_DOUBLE_TAP:
                self.double_tap = True
            elif gesture == GESTURE_SWIPE_RIGHT:
                self.swipe_right = True

        else:
            # PC: キーボード入力
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.button_a_pressed = True
                    elif event.key == pygame.K_x:
                        self.button_b_pressed = True
                    elif event.key == pygame.K_c:
                        self.double_tap = True    # C キー = ダブルタップ
                    elif event.key == pygame.K_v:
                        self.swipe_right = True   # V キー = 右スワイプ

    def cleanup(self):
        """GPIO・タッチ後始末"""
        self.touch.cleanup()
        if IS_RASPBERRY_PI and GPIO:
            GPIO.cleanup()
