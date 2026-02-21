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
GESTURE_LONG_PRESS  = 0x0C


class TouchHandler:
    """CST816S タッチパネルを I2C + INTピンポーリングで読み取るクラス

    GPIO.add_event_detect() を使わず、poll() を毎フレーム呼ぶ方式。
    INTピンが HIGH→LOW になった瞬間に I2C を読み取る。
    """

    def __init__(self):
        self.smbus = None
        self._pending_gesture = GESTURE_NONE
        self._last_int = 1       # 前回のINTピンの状態（1=HIGH）
        self._touch_active = False  # タッチ中フラグ（LOW→HIGH時にタップ判定用）

        if not IS_RASPBERRY_PI:
            return
        try:
            import smbus2
            if GPIO:
                GPIO.setwarnings(False)
                # RST: タッチコントローラーをリセット
                try:
                    GPIO.setup(TOUCH_RST_PIN, GPIO.OUT)
                    GPIO.output(TOUCH_RST_PIN, GPIO.LOW)
                    time.sleep(0.05)
                    GPIO.output(TOUCH_RST_PIN, GPIO.HIGH)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"タッチRSTエラー（無視）: {e}")
                # INT: 入力ピンとして設定（edge detectionは使わない）
                try:
                    GPIO.setup(TOUCH_INT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                except Exception as e:
                    print(f"タッチINTセットアップエラー（無視）: {e}")

            self.smbus = smbus2.SMBus(1)
            # MOTION_MASK (0xEC): Bit0=EnDClick(ダブルタップ有効)
            self.smbus.write_byte_data(TOUCH_I2C_ADDR, 0xEC, 0x01)
            time.sleep(0.01)
            # IRQ_CTL (0xFA): Bit6=EnTouch, Bit5=EnChange, Bit4=EnMotion
            self.smbus.write_byte_data(TOUCH_I2C_ADDR, 0xFA, 0x70)
            time.sleep(0.01)
            print("タッチパネル初期化完了")
        except Exception as e:
            print(f"タッチパネル初期化エラー（無視）: {e}")
            self.smbus = None

    def poll(self):
        """毎フレーム呼ぶ。INTピンの変化を両方向で検出してI2Cを読む"""
        if not self.smbus or not GPIO:
            return
        try:
            current_int = GPIO.input(TOUCH_INT_PIN)

            # 立ち下がり（HIGH→LOW）: タッチ開始 → スワイプは即座に確定
            if self._last_int == 1 and current_int == 0:
                data = self.smbus.read_i2c_block_data(TOUCH_I2C_ADDR, 0x00, 7)
                gesture = data[1]
                print(f"[TOUCH] falling gesture=0x{gesture:02X}")
                if self._pending_gesture == GESTURE_NONE:
                    # スワイプ系（0x01〜0x04）は立ち下がりで即確定（高感度）
                    if gesture in (GESTURE_SWIPE_UP, GESTURE_SWIPE_DOWN,
                                   GESTURE_SWIPE_LEFT, GESTURE_SWIPE_RIGHT):
                        self._pending_gesture = gesture
                    elif gesture != GESTURE_NONE:
                        self._pending_gesture = gesture
                self._touch_active = True

            # 立ち上がり（LOW→HIGH）: 指を離した → タップ確定
            elif self._last_int == 0 and current_int == 1:
                data = self.smbus.read_i2c_block_data(TOUCH_I2C_ADDR, 0x00, 7)
                gesture = data[1]
                print(f"[TOUCH] rising gesture=0x{gesture:02X}")
                if self._pending_gesture == GESTURE_NONE:
                    if gesture != GESTURE_NONE:
                        self._pending_gesture = gesture
                    elif self._touch_active:
                        # gesture=0x00で離したらシングルタップとみなす
                        print(f"[TOUCH] tap by release")
                        self._pending_gesture = GESTURE_CLICK
                self._touch_active = False

            self._last_int = current_int
        except Exception as e:
            print(f"[TOUCH] ポーリングエラー: {e}")

    def consume_gesture(self):
        """保存されたジェスチャーを1度だけ返してリセット"""
        gesture = self._pending_gesture
        self._pending_gesture = GESTURE_NONE
        return gesture

    def cleanup(self):
        if self.smbus:
            self.smbus.close()


class InputHandler:
    """ボタン・タッチ入力を抽象化するクラス

    Raspberry Pi: GPIO ボタン + タッチパネル
    PC: キーボード (Z=ボタンA, X=ボタンB, C=タップ, V=右スワイプ)
    """

    def __init__(self):
        self.button_a_pressed = False   # 録音開始
        self.button_b_pressed = False   # アーカイブ表示
        self.double_tap = False         # タップ → 録音開始
        self.swipe_left  = False        # 左スワイプ → アーカイブ表示
        self.swipe_right = False        # 右スワイプ → メイン画面に戻る
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
        self.swipe_left  = False
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

            # タッチパネルをポーリング
            self.touch.poll()
            gesture = self.touch.consume_gesture()
            # タップ・ダブルタップ・ロングプレス → 録音開始
            if gesture in (GESTURE_CLICK, GESTURE_DOUBLE_TAP, GESTURE_LONG_PRESS):
                self.double_tap = True
            # 左スワイプ(0x03) → アーカイブへ
            elif gesture == GESTURE_SWIPE_LEFT:
                self.swipe_right = True
            # 右スワイプ(0x04) → メイン画面に戻る
            elif gesture == GESTURE_SWIPE_RIGHT:
                self.swipe_left = True

        else:
            # PC: キーボード入力
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.button_a_pressed = True
                    elif event.key == pygame.K_x:
                        self.button_b_pressed = True
                    elif event.key == pygame.K_c:
                        self.double_tap = True    # C キー = タップ（録音）
                    elif event.key == pygame.K_b:
                        self.swipe_left = True    # B キー = 左スワイプ（アーカイブ）
                    elif event.key == pygame.K_v:
                        self.swipe_right = True   # V キー = 右スワイプ（メインに戻る）

    def cleanup(self):
        """GPIO・タッチ後始末"""
        self.touch.cleanup()
        if IS_RASPBERRY_PI and GPIO:
            GPIO.cleanup()
