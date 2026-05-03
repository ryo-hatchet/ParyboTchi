"""BGM と効果音の再生。pygame.mixer ベース。"""
from __future__ import annotations

from pathlib import Path

import pygame

from nomiboy.config import ASSETS_DIR


class AudioService:
    def __init__(self, base_dir: Path = ASSETS_DIR, master_volume: float = 0.7) -> None:
        self._base = base_dir
        self._sfx_cache: dict[str, pygame.mixer.Sound] = {}
        self._master = master_volume
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        try:
            pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=4096)
        except pygame.error:
            # ヘッドレス・音声デバイスなしの環境（テスト等）では初期化失敗を許容
            pass

    def set_master_volume(self, v: float) -> None:
        self._master = max(0.0, min(1.0, v))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self._master)

    def play_se(self, name: str) -> None:
        if not pygame.mixer.get_init():
            return
        s = self._sfx_cache.get(name)
        if s is None:
            path = self._base / "sfx" / name
            if not path.exists():
                return
            s = pygame.mixer.Sound(str(path))
            self._sfx_cache[name] = s
        s.set_volume(self._master)
        s.play()

    def play_bgm(self, name: str, loop: bool = True) -> None:
        if not pygame.mixer.get_init():
            return
        path = self._base / "bgm" / name
        if not path.exists():
            return
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(self._master)
        pygame.mixer.music.play(-1 if loop else 0)

    def stop_bgm(self) -> None:
        if not pygame.mixer.get_init():
            return
        pygame.mixer.music.stop()
