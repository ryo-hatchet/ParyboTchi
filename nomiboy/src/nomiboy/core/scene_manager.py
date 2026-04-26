"""Scene のスタック管理。push/pop/replace/reset_to を提供。"""
from __future__ import annotations

from typing import Any

from .scene import Scene


class SceneManager:
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx
        self._stack: list[Scene] = []

    @property
    def current(self) -> Scene | None:
        return self._stack[-1] if self._stack else None

    @property
    def depth(self) -> int:
        return len(self._stack)

    def push(self, scene: Scene) -> None:
        if self._stack:
            self._stack[-1].on_exit()
        self._stack.append(scene)
        scene.on_enter(self._ctx)

    def pop(self) -> None:
        if not self._stack:
            return
        top = self._stack.pop()
        top.on_exit()
        if self._stack:
            self._stack[-1].on_enter(self._ctx)

    def replace(self, scene: Scene) -> None:
        if self._stack:
            self._stack[-1].on_exit()
            self._stack.pop()
        self._stack.append(scene)
        scene.on_enter(self._ctx)

    def reset_to(self, scene: Scene) -> None:
        # top シーンのみ on_exit（それ以下は push 時に既に exit 済み）
        if self._stack:
            self._stack[-1].on_exit()
        self._stack.clear()
        self._stack.append(scene)
        scene.on_enter(self._ctx)

    def handle_event(self, event: Any) -> None:
        if self._stack:
            self._stack[-1].handle_event(event)

    def update(self, dt: float) -> None:
        if self._stack:
            self._stack[-1].update(dt)

    def draw(self, surface) -> None:
        if self._stack:
            self._stack[-1].draw(surface)
