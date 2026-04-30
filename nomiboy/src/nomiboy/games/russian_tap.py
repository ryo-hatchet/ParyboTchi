"""ロシアン飲酒。3×3 マスのうち1マスに爆弾、順番にタップして引いた人が飲む。"""
from __future__ import annotations

import random

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class RussianTapController:
    """純ロジック。9 マスのうち1マスに爆弾、ターン制で誰か引くまで進む。"""

    BOARD_SIZE: int = 9  # 3×3

    def __init__(
        self,
        player_count: int,
        rng: random.Random | None = None,
    ) -> None:
        self._n = player_count
        self._rng = rng or random.Random()
        self._bomb_cell: int = -1
        self._current_player_index: int = 0
        self._safe_cells: set[int] = set()
        self._exploded: bool = False
        self._loser_index: int | None = None
        self._started: bool = False

    @property
    def current_player_index(self) -> int:
        return self._current_player_index

    @property
    def safe_cells(self) -> set[int]:
        return self._safe_cells

    @property
    def exploded(self) -> bool:
        return self._exploded

    @property
    def loser_index(self) -> int | None:
        return self._loser_index

    def start(self) -> None:
        self._bomb_cell = self._rng.randrange(self.BOARD_SIZE)
        self._current_player_index = self._rng.randrange(self._n)
        self._safe_cells = set()
        self._exploded = False
        self._loser_index = None
        self._started = True

    def tap(self, cell_index: int) -> bool:
        """指定マスをタップ。爆弾なら True、セーフ・no-op なら False。"""
        if not self._started or self._exploded:
            return False
        if not 0 <= cell_index < self.BOARD_SIZE:
            return False
        if cell_index in self._safe_cells:
            return False
        if cell_index == self._bomb_cell:
            self._exploded = True
            self._loser_index = self._current_player_index
            return True
        self._safe_cells.add(cell_index)
        self._current_player_index = (self._current_player_index + 1) % self._n
        return False


# ─────────────── Scene ───────────────

# レイアウト定数
_HEADER_H = 50
_GRID_TOP = 70
_CELL_SIZE = 72
_CELL_GAP = 12
_GRID_COLS = 3
_GRID_ROWS = 3
_GRID_W = _CELL_SIZE * _GRID_COLS + _CELL_GAP * (_GRID_COLS - 1)  # 240
_GRID_LEFT = (config.SCREEN_SIZE[0] - _GRID_W) // 2  # 120

# 爆発演出
_FLASH_DURATION = 0.6  # 秒
_FLASH_BLINKS = 3


class RussianTapScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._ctrl: RussianTapController | None = None
        self._title_r: TextRenderer | None = None
        self._cell_r: TextRenderer | None = None
        self._boom_r: TextRenderer | None = None
        self._buttons: list[Button] = []
        self._cell_rects: list[pygame.Rect] = []
        self._explosion_timer: float = 0.0
        self._exploded_handled: bool = False

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 22), colors.INK_LIGHT
        )
        self._cell_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 28), colors.INK_DARK
        )
        self._boom_r = TextRenderer(
            ctx.assets.font("DotGothic16-Regular.ttf", 48), colors.INK_LIGHT
        )
        self._ctrl = RussianTapController(player_count=ctx.players.count)
        self._ctrl.start()
        self._explosion_timer = 0.0
        self._exploded_handled = False
        self._buttons = [
            Button(
                pygame.Rect(10, 10, 80, 26),
                "BACK",
                self._sm.pop,
                bg_color=colors.ACCENT_BERRY,
                fg_color=colors.INK_LIGHT,
            ),
        ]
        self._cell_rects = [
            pygame.Rect(
                _GRID_LEFT + (i % _GRID_COLS) * (_CELL_SIZE + _CELL_GAP),
                _GRID_TOP + (i // _GRID_COLS) * (_CELL_SIZE + _CELL_GAP),
                _CELL_SIZE,
                _CELL_SIZE,
            )
            for i in range(_GRID_COLS * _GRID_ROWS)
        ]

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return
        if self._ctrl is None or self._ctrl.exploded or event.kind != InputKind.TAP:
            return
        for i, rect in enumerate(self._cell_rects):
            if rect.collidepoint(event.x, event.y):
                self._ctrl.tap(i)
                return

    def update(self, dt: float) -> None:
        if self._ctrl is None:
            return
        if self._ctrl.exploded:
            self._explosion_timer += dt
            if (
                not self._exploded_handled
                and self._explosion_timer >= _FLASH_DURATION
            ):
                self._exploded_handled = True
                from nomiboy.scenes.result import ResultScene

                loser = self._ctx.players.players[self._ctrl.loser_index]
                self._sm.push(ResultScene(self._sm, loser))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._draw_header(surface)
        self._draw_grid(surface)
        if self._ctrl is not None and self._ctrl.exploded:
            self._draw_explosion(surface)
        for b in self._buttons:
            b.draw(surface, self._cell_r)

    # ── 内部 ──

    def _draw_header(self, surface: pygame.Surface) -> None:
        if self._ctrl is None or self._ctx is None:
            return
        idx = (
            self._ctrl.loser_index
            if self._ctrl.exploded
            else self._ctrl.current_player_index
        )
        player = self._ctx.players.players[idx]
        pygame.draw.rect(
            surface,
            player.color,
            pygame.Rect(0, 0, config.SCREEN_SIZE[0], _HEADER_H),
        )
        label = (
            f"{player.name} ばくはつ！"
            if self._ctrl.exploded
            else f"{player.name} の ばん"
        )
        self._title_r.draw(
            surface,
            label,
            (config.SCREEN_SIZE[0] // 2, _HEADER_H // 2),
            anchor="center",
            color=colors.INK_LIGHT,
        )

    def _draw_grid(self, surface: pygame.Surface) -> None:
        if self._ctrl is None:
            return
        for i, rect in enumerate(self._cell_rects):
            if self._ctrl.exploded and i == self._ctrl_bomb_cell():
                bg = colors.DANGER_RED
                label = "💣"
            elif i in self._ctrl.safe_cells:
                bg = (160, 160, 160)
                label = "×"
            else:
                bg = colors.BG_SECONDARY
                label = "?"
            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, colors.INK_DARK, rect, width=2)
            self._cell_r.draw(
                surface, label, rect.center, anchor="center", color=colors.INK_DARK
            )

    def _draw_explosion(self, surface: pygame.Surface) -> None:
        # 赤フラッシュ（点滅3回）
        phase = (self._explosion_timer / _FLASH_DURATION) * (_FLASH_BLINKS * 2)
        if int(phase) % 2 == 0:
            flash = pygame.Surface(config.SCREEN_SIZE, flags=pygame.SRCALPHA)
            flash.fill((*colors.DANGER_RED, 140))
            surface.blit(flash, (0, 0))
        self._boom_r.draw(
            surface,
            "BOOM!!",
            (config.SCREEN_SIZE[0] // 2, config.SCREEN_SIZE[1] // 2),
            anchor="center",
            color=colors.INK_LIGHT,
        )

    def _ctrl_bomb_cell(self) -> int:
        # Scene 側で爆弾マスを赤く描画するため、爆発時のみ参照（テストヘルパと同じパス）
        return self._ctrl._bomb_cell  # noqa: SLF001
