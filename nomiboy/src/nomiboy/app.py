"""nomiboy の起動とメインループ。AppContext を保持して各 Scene に渡す。"""
from __future__ import annotations

import logging
import os
import socket
from dataclasses import dataclass

import pygame

from nomiboy import config
from nomiboy.colors import BG_PRIMARY, DANGER_RED
from nomiboy.core.asset_loader import AssetLoader
from nomiboy.core.audio_service import AudioService
from nomiboy.core.input_adapter import InputAdapter
from nomiboy.core.scene_manager import SceneManager
from nomiboy.core.tts_service import TTSService
from nomiboy.stores.player_store import PlayerStore

log = logging.getLogger(__name__)


@dataclass
class AppContext:
    config: object
    input_adapter: InputAdapter
    audio: AudioService
    tts: TTSService
    players: PlayerStore
    assets: AssetLoader
    online: bool


def _check_online(host: str = "generativelanguage.googleapis.com", port: int = 443, timeout: float = 5.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


class App:
    def __init__(self) -> None:
        pygame.init()
        flags = pygame.FULLSCREEN if config.FULLSCREEN else 0
        self._screen = pygame.display.set_mode(config.SCREEN_SIZE, flags)
        pygame.display.set_caption("nomiboy")
        if config.HIDE_CURSOR:
            pygame.mouse.set_visible(False)
        self._clock = pygame.time.Clock()
        self._running = True

        api_key = os.environ.get("GEMINI_API_KEY")
        self.ctx = AppContext(
            config=config,
            input_adapter=InputAdapter(config.SCREEN_SIZE),
            audio=AudioService(),
            tts=TTSService(api_key=api_key),
            players=PlayerStore(),
            assets=AssetLoader(),
            online=_check_online(),
        )
        self.sm = SceneManager(ctx=self.ctx)

    def push_initial_scene(self) -> None:
        from nomiboy.scenes.title import TitleScene
        self.sm.push(TitleScene(self.sm))

    def run(self) -> None:
        self.push_initial_scene()
        while self._running:
            dt = self._clock.tick(config.TARGET_FPS) / 1000.0
            for pg_event in pygame.event.get():
                if pg_event.type == pygame.QUIT:
                    self._running = False
                    break
                if pg_event.type == pygame.KEYDOWN and pg_event.key == pygame.K_ESCAPE:
                    self._running = False
                    break
                ev = self.ctx.input_adapter.translate(pg_event)
                if ev is not None:
                    try:
                        self.sm.handle_event(ev)
                    except Exception:
                        log.exception("Scene event error")
                        self._show_fatal_error()
            try:
                self.sm.update(dt)
                self._screen.fill(BG_PRIMARY)
                self.sm.draw(self._screen)
            except Exception:
                log.exception("Scene update/draw error")
                self._show_fatal_error()
            pygame.display.flip()
        pygame.quit()

    def _show_fatal_error(self) -> None:
        font = pygame.font.Font(None, 36)
        msg = font.render("エラーが発生しました", True, DANGER_RED)
        self._screen.fill((0, 0, 0))
        self._screen.blit(msg, msg.get_rect(center=(config.SCREEN_SIZE[0] // 2, config.SCREEN_SIZE[1] // 2)))
        pygame.display.flip()
        pygame.time.delay(5000)
        from nomiboy.scenes.title import TitleScene
        self.sm.reset_to(TitleScene(self.sm))
