"""ParyboTchi - キャラクター描画モジュール（画像ベース）

assets/ フォルダの表情画像を切り替えて表示する。
  - character_normal.png    : 通常
  - character_blink.png     : 瞬き（目を閉じた状態）
  - character_listening.png : 音楽を聴いている
  - character_happy.png     : 嬉しい（曲を見つけた）
  - Angry.jpg               : 不機嫌（24時間以上音楽を聴いていない）

画像が見つからない場合はフォールバックとして簡易描画を行う。
"""

import math
import os
import random
import pygame

from config import SCREEN_SIZE, SCREEN_CENTER, CHARACTER_IMAGES


class Character:
    """画像ベースのParyboTchiキャラクター"""

    # 瞬きの設定
    BLINK_INTERVAL_MIN = 2.0   # 最短瞬き間隔（秒）
    BLINK_INTERVAL_MAX = 5.0   # 最長瞬き間隔（秒）
    BLINK_DURATION = 0.15      # 瞬きの持続時間（秒）

    def __init__(self):
        self.blink_timer = 0
        self.is_blinking = False
        self._next_blink = random.uniform(self.BLINK_INTERVAL_MIN,
                                          self.BLINK_INTERVAL_MAX)
        self.bounce_offset = 0
        self.bounce_timer = 0
        self.emotion = "normal"  # normal, listening, happy
        self.note_angle = 0.0

        # 画像キャッシュ
        self._images = {}
        self._images_loaded = False

    @staticmethod
    def _crop_center_square(surface):
        """画像の中央から正方形にクロップする。

        16:9 などの横長画像 → 高さに合わせて中央の正方形を切り出す。
        縦長画像 → 幅に合わせて中央の正方形を切り出す。
        正方形ならそのまま返す。
        """
        w, h = surface.get_size()
        if w == h:
            return surface

        side = min(w, h)
        x = (w - side) // 2
        y = (h - side) // 2
        return surface.subsurface(pygame.Rect(x, y, side, side)).copy()

    def _load_images(self):
        """画像をロードしてキャッシュ

        16:9 等の非正方形画像は中央クロップ → 240x240 にリサイズ。
        """
        self._images_loaded = True
        for emotion, path in CHARACTER_IMAGES.items():
            if os.path.isfile(path):
                try:
                    raw = pygame.image.load(path)
                    # PNG(アルファあり) と JPEG(アルファなし) の両方に対応
                    if raw.get_alpha() is not None or path.lower().endswith(".png"):
                        img = raw.convert_alpha()
                    else:
                        img = raw.convert()
                    # 中央から正方形にクロップ
                    img = self._crop_center_square(img)
                    # SCREEN_SIZE にリサイズ
                    img = pygame.transform.smoothscale(
                        img, (SCREEN_SIZE, SCREEN_SIZE))
                    self._images[emotion] = img
                except pygame.error:
                    pass

        # 画像がない表情は代用画像で埋める
        if "normal" in self._images:
            # listening がなければ normal で代用
            if "listening" not in self._images:
                self._images["listening"] = self._images["normal"]
            # happy がなければ listening → normal の順で代用
            if "happy" not in self._images:
                self._images["happy"] = self._images.get(
                    "listening", self._images["normal"])
            # blink がなければ normal で代用
            if "blink" not in self._images:
                self._images["blink"] = self._images["normal"]
            # angry がなければ normal で代用
            if "angry" not in self._images:
                self._images["angry"] = self._images["normal"]

    def update(self, dt):
        """アニメーション更新"""
        self.bounce_timer += dt

        # バウンス（画像全体を上下に揺らす）
        if self.emotion == "happy":
            self.bounce_offset = math.sin(self.bounce_timer * 7) * 4
        elif self.emotion == "listening":
            self.bounce_offset = math.sin(self.bounce_timer * 3) * 2
        else:
            # ゆっくりした呼吸アニメーション（±3px）
            self.bounce_offset = math.sin(self.bounce_timer * 1.5) * 3

        self.note_angle += dt * 2.5

        # 瞬きロジック（normal / listening / angry のときのみ）
        if self.emotion in ("normal", "listening", "angry"):
            self.blink_timer += dt
            if self.is_blinking:
                # 瞬き中 → 持続時間が過ぎたら終了
                if self.blink_timer >= self.BLINK_DURATION:
                    self.is_blinking = False
                    self.blink_timer = 0
                    self._next_blink = random.uniform(
                        self.BLINK_INTERVAL_MIN, self.BLINK_INTERVAL_MAX)
            else:
                # 通常 → 次の瞬きまでのカウントダウン
                if self.blink_timer >= self._next_blink:
                    self.is_blinking = True
                    self.blink_timer = 0
        else:
            # happy のときは瞬きしない（リセット）
            self.is_blinking = False
            self.blink_timer = 0

    def draw(self, surface, stage_name, alpha=255):
        """キャラクターを描画"""
        if not self._images_loaded:
            self._load_images()

        if self._images:
            self._draw_image(surface, alpha=alpha)
        else:
            self._draw_fallback(surface)

    def _draw_image(self, surface, alpha=255):
        """画像で描画"""
        # 瞬き中はblinkを優先表示
        if self.is_blinking and "blink" in self._images:
            img = self._images["blink"]
        else:
            img = self._images.get(self.emotion, self._images.get("normal"))

        if img is None:
            return

        # バウンスオフセット + 5px 下にずらす
        y_offset = int(self.bounce_offset) + 5
        if alpha < 255:
            temp = img.copy()
            temp.set_alpha(alpha)
            surface.blit(temp, (0, y_offset))
        else:
            surface.blit(img, (0, y_offset))

    def _draw_fallback(self, surface):
        """画像がない場合のフォールバック（シンプルな顔）"""
        cx, cy = SCREEN_CENTER, SCREEN_CENTER + int(self.bounce_offset)
        r = 50

        # 体
        pygame.draw.circle(surface, (200, 200, 200), (cx, cy), r)
        pygame.draw.circle(surface, (100, 100, 100), (cx, cy), r, 2)

        # 目
        eye_y = cy - 8
        for side in [-1, 1]:
            ex = cx + side * 18
            if self.is_blinking:
                # 瞬き中は横線で目を閉じた表現
                pygame.draw.line(surface, (30, 30, 30),
                                 (ex - 6, eye_y), (ex + 6, eye_y), 2)
            else:
                pygame.draw.circle(surface, (255, 255, 255), (ex, eye_y), 8)
                pygame.draw.circle(surface, (30, 30, 30), (ex, eye_y), 4)
                pygame.draw.circle(surface, (255, 255, 255),
                                   (ex - 2, eye_y - 2), 2)

        # 口
        if self.emotion == "happy":
            pygame.draw.arc(surface, (60, 60, 60),
                            (cx - 12, cy + 5, 24, 14), 3.4, 6.0, 2)
        elif self.emotion == "angry":
            # への字口（不機嫌）
            pygame.draw.arc(surface, (60, 60, 60),
                            (cx - 12, cy + 8, 24, 14), 0.2, 3.0, 2)
        else:
            pygame.draw.line(surface, (60, 60, 60),
                             (cx - 8, cy + 12), (cx + 8, cy + 12), 2)
