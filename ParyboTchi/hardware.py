"""ParyboTchi - ハードウェア入力モジュール（GPIO / キーボード抽象化）"""

import pygame
from config import IS_RASPBERRY_PI, BUTTON_A_PIN, BUTTON_B_PIN

GPIO = None
if IS_RASPBERRY_PI:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        pass


class InputHandler:
    """ボタン入力を抽象化するクラス

    Raspberry Pi: GPIOボタン
    PC: キーボード (Z=ボタンA, X=ボタンB)
    """

    def __init__(self):
        self.button_a_pressed = False
        self.button_b_pressed = False
        self._prev_a = False
        self._prev_b = False

        if IS_RASPBERRY_PI and GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUTTON_A_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(BUTTON_B_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def update(self, events):
        """入力状態を更新。押した瞬間だけTrueになる（エッジ検出）"""
        self.button_a_pressed = False
        self.button_b_pressed = False

        if IS_RASPBERRY_PI and GPIO:
            a = not GPIO.input(BUTTON_A_PIN)  # プルアップなので反転
            b = not GPIO.input(BUTTON_B_PIN)
            if a and not self._prev_a:
                self.button_a_pressed = True
            if b and not self._prev_b:
                self.button_b_pressed = True
            self._prev_a = a
            self._prev_b = b
        else:
            # PC: キーボード入力
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.button_a_pressed = True
                    elif event.key == pygame.K_x:
                        self.button_b_pressed = True

    def cleanup(self):
        """GPIO後始末"""
        if IS_RASPBERRY_PI and GPIO:
            GPIO.cleanup()
