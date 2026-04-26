"""単一 Scene を直接起動するデバッグツール。

例:
  python scripts/run_scene.py title
  python scripts/run_scene.py odai --players たろう,はなこ
  python scripts/run_scene.py bomb --players a,b,c,d
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

os.environ.setdefault("NOMIBOY_FULLSCREEN", "0")

import pygame  # noqa: E402

from nomiboy.app import App  # noqa: E402


SCENE_FACTORIES = {
    "title": lambda app: __import__("nomiboy.scenes.title", fromlist=["TitleScene"]).TitleScene(app.sm),
    "register": lambda app: __import__("nomiboy.scenes.player_register", fromlist=["PlayerRegisterScene"]).PlayerRegisterScene(app.sm),
    "select": lambda app: __import__("nomiboy.scenes.game_select", fromlist=["GameSelectScene"]).GameSelectScene(app.sm),
    "bomb": lambda app: __import__("nomiboy.games.bomb", fromlist=["BombScene"]).BombScene(app.sm),
    "roulette": lambda app: __import__("nomiboy.games.roulette", fromlist=["RouletteScene"]).RouletteScene(app.sm),
    "odai": lambda app: __import__("nomiboy.games.odai", fromlist=["OdaiScene"]).OdaiScene(app.sm),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene", choices=list(SCENE_FACTORIES.keys()))
    parser.add_argument("--players", default="", help="comma-separated names")
    args = parser.parse_args()

    app = App()
    if args.players:
        for name in args.players.split(","):
            n = name.strip()
            if n:
                app.ctx.players.add(n)
    app.sm.push(SCENE_FACTORIES[args.scene](app))

    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(30) / 1000.0
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                break
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                running = False
                break
            ev = app.ctx.input_adapter.translate(e)
            if ev is not None:
                app.sm.handle_event(ev)
        app.sm.update(dt)
        app._screen.fill((255, 203, 5))
        app.sm.draw(app._screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
