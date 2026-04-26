# nomiboy 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raspberry Pi Zero 2 + 3.5"SPIタッチ + I2Sスピーカー上で動作する飲みゲー集合機 nomiboy（爆弾タイマー / ルーレット / お題ゲーム）を Pygame で実装し、PC でも同一コードでデバッグ可能な状態にする。

**Architecture:** Scene 抽象クラス + SceneManager（push/pop スタック）でナビゲーションを管理。Core サービス（InputAdapter/AudioService/TTSService/PlayerStore/AssetLoader）を AppContext から DI で各 Scene に注入。タッチイベントとマウスイベントは InputAdapter で `InputEvent` に統一。ハード差分は `Config.IS_PI` 1箇所で吸収。

**Tech Stack:** Python 3.11 / Pygame 2.5+ / google-genai（TTS）/ pytest（ヘッドレス: SDL_VIDEODRIVER=dummy）/ ruff / systemd（Pi 自動起動）

**Reference Spec:** `nomiboy/docs/superpowers/specs/2026-04-26-nomiboy-design.md`

---

## ファイル構成（実装後）

```
nomiboy/
├── DESIGN.md                            # GBC 風（Task 27 で新規作成）
├── DESIGN.legacy.md                      # Superhuman 風（Task 2 でリネーム）
├── README.md                            # Task 26
├── requirements.txt                     # Task 1
├── pyproject.toml                       # Task 1
├── .env.example                         # Task 26
│
├── src/nomiboy/
│   ├── __init__.py
│   ├── main.py                          # Task 15
│   ├── app.py                           # Task 15
│   ├── config.py                        # Task 4
│   ├── colors.py                        # Task 5
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scene.py                     # Task 7
│   │   ├── scene_manager.py             # Task 7
│   │   ├── input_adapter.py             # Task 8
│   │   ├── asset_loader.py              # Task 9
│   │   ├── audio_service.py             # Task 10
│   │   ├── tts_service.py               # Task 11
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── text.py                  # Task 12
│   │       ├── button.py                # Task 13
│   │       └── keyboard.py              # Task 14
│   │
│   ├── stores/
│   │   ├── __init__.py
│   │   └── player_store.py              # Task 6
│   │
│   ├── scenes/
│   │   ├── __init__.py
│   │   ├── title.py                     # Task 16
│   │   ├── player_register.py           # Task 17
│   │   ├── keyboard_input.py            # Task 18
│   │   ├── game_select.py               # Task 19
│   │   └── result.py                    # Task 20
│   │
│   └── games/
│       ├── __init__.py                  # Task 21
│       ├── bomb.py                      # Task 21
│       ├── roulette.py                  # Task 22
│       └── odai.py                      # Task 23
│
├── assets/                               # Task 1（空ディレクトリ作成）
│   ├── fonts/
│   ├── images/
│   ├── sfx/
│   ├── bgm/
│   └── tts_cache/
│
├── data/
│   └── odai_cards.json                  # Task 23
│
├── tests/
│   ├── conftest.py                      # Task 3
│   ├── test_config.py                   # Task 4
│   ├── test_player_store.py             # Task 6
│   ├── test_scene_manager.py            # Task 7
│   ├── test_input_adapter.py            # Task 8
│   ├── test_tts_service.py              # Task 11
│   ├── test_keyboard_widget.py          # Task 14
│   └── games/
│       ├── __init__.py
│       ├── test_bomb.py                 # Task 21
│       ├── test_roulette.py             # Task 22
│       └── test_odai.py                 # Task 23
│
└── scripts/
    ├── run_pc.sh                        # Task 24
    ├── run_scene.py                     # Task 24
    ├── install_pi.sh                    # Task 25
    └── nomiboy.service                  # Task 25
```

**実装順は依存に従う：基礎 → Core ロジック層 → Core IO 層 → ウィジェット → 骨格 → シーン → ゲーム → ツール。** 各タスクは前のタスクの成果に依存するため、順番通りに実行すること。

---

# Phase 0: プロジェクトセットアップ

## Task 1: プロジェクトスケルトン

**Files:**
- Create: `nomiboy/pyproject.toml`
- Create: `nomiboy/requirements.txt`
- Create: `nomiboy/src/nomiboy/__init__.py`
- Create: `nomiboy/src/nomiboy/core/__init__.py`
- Create: `nomiboy/src/nomiboy/core/widgets/__init__.py`
- Create: `nomiboy/src/nomiboy/stores/__init__.py`
- Create: `nomiboy/src/nomiboy/scenes/__init__.py`
- Create: `nomiboy/src/nomiboy/games/__init__.py`
- Create: `nomiboy/tests/__init__.py`
- Create: `nomiboy/tests/games/__init__.py`
- Create: `nomiboy/assets/{fonts,images,sfx,bgm,tts_cache}/.gitkeep`
- Create: `nomiboy/data/.gitkeep`
- Create: `nomiboy/scripts/.gitkeep`

- [ ] **Step 1: ディレクトリ構造を作成**

```bash
cd nomiboy
mkdir -p src/nomiboy/core/widgets src/nomiboy/stores src/nomiboy/scenes src/nomiboy/games
mkdir -p tests/games
mkdir -p assets/fonts assets/images assets/sfx assets/bgm assets/tts_cache
mkdir -p data scripts
touch src/nomiboy/__init__.py src/nomiboy/core/__init__.py src/nomiboy/core/widgets/__init__.py
touch src/nomiboy/stores/__init__.py src/nomiboy/scenes/__init__.py src/nomiboy/games/__init__.py
touch tests/__init__.py tests/games/__init__.py
touch assets/fonts/.gitkeep assets/images/.gitkeep assets/sfx/.gitkeep assets/bgm/.gitkeep assets/tts_cache/.gitkeep
touch data/.gitkeep scripts/.gitkeep
```

- [ ] **Step 2: `requirements.txt` を作成**

```
pygame>=2.5.0
google-genai>=0.3.0
python-dotenv>=1.0.0
requests>=2.31.0
```

- [ ] **Step 3: `pyproject.toml` を作成**

```toml
[project]
name = "nomiboy"
version = "0.1.0"
description = "飲みゲー集合機 (Drinking games console for Raspberry Pi)"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP"]
```

- [ ] **Step 4: 仮想環境作成と依存インストール**

```bash
cd nomiboy
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pytest ruff
```

期待値：エラーなく完了。

- [ ] **Step 5: コミット**

```bash
git add nomiboy/pyproject.toml nomiboy/requirements.txt nomiboy/src nomiboy/tests nomiboy/assets nomiboy/data nomiboy/scripts
git commit -m "nomiboy: プロジェクトスケルトンと依存定義を追加"
```

---

## Task 2: 既存 DESIGN.md をアーカイブ

**Files:**
- Rename: `nomiboy/DESIGN.md` → `nomiboy/DESIGN.legacy.md`

- [ ] **Step 1: ファイルをリネーム**

```bash
cd nomiboy
git mv DESIGN.md DESIGN.legacy.md
```

- [ ] **Step 2: 旧ファイルの先頭にアーカイブ注記を追加**（`DESIGN.legacy.md` の冒頭に1行挿入）

```markdown
> **アーカイブ：** これは Superhuman 風デザインの旧仕様です。GBC 風に方針変更したため `DESIGN.md`（新規）を参照してください。

# Design System Inspiration of Superhuman
（既存内容はそのまま）
```

- [ ] **Step 3: コミット**

```bash
git add nomiboy/DESIGN.legacy.md
git commit -m "nomiboy: 旧 DESIGN.md を DESIGN.legacy.md にアーカイブ"
```

---

## Task 3: pytest conftest（ヘッドレス Pygame）

**Files:**
- Create: `nomiboy/tests/conftest.py`

- [ ] **Step 1: `conftest.py` を作成**

```python
"""pytest 全テストでヘッドレス pygame を使う設定。"""
import os

# pygame.init() の前にダミードライバ指定（音声・映像なし）
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
```

- [ ] **Step 2: 動作確認の最小テストを作成**

`nomiboy/tests/test_smoke.py`:
```python
def test_pygame_can_init_headless():
    import pygame
    pygame.init()
    assert pygame.get_init()
    pygame.quit()
```

- [ ] **Step 3: テストを実行**

```bash
cd nomiboy && source venv/bin/activate && pytest tests/test_smoke.py -v
```

期待値：PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/tests/conftest.py nomiboy/tests/test_smoke.py
git commit -m "nomiboy: pytest をヘッドレス pygame で動かす設定"
```

---

# Phase 1: 基礎モジュール

## Task 4: Config モジュール

**Files:**
- Create: `nomiboy/src/nomiboy/config.py`
- Create: `nomiboy/tests/test_config.py`

- [ ] **Step 1: 失敗するテストを書く**

`nomiboy/tests/test_config.py`:
```python
import os
from nomiboy import config


def test_screen_size_is_landscape_480x320():
    assert config.SCREEN_SIZE == (480, 320)


def test_target_fps_is_30():
    assert config.TARGET_FPS == 30


def test_is_pi_can_be_overridden_by_env(monkeypatch):
    monkeypatch.setenv("NOMIBOY_FORCE_PI", "1")
    is_pi = config.detect_is_pi()
    assert is_pi is True


def test_fullscreen_follows_is_pi(monkeypatch):
    monkeypatch.setenv("NOMIBOY_FORCE_PI", "1")
    monkeypatch.delenv("NOMIBOY_FULLSCREEN", raising=False)
    assert config.detect_fullscreen() is True


def test_fullscreen_can_be_overridden(monkeypatch):
    monkeypatch.setenv("NOMIBOY_FORCE_PI", "1")
    monkeypatch.setenv("NOMIBOY_FULLSCREEN", "0")
    assert config.detect_fullscreen() is False
```

- [ ] **Step 2: テスト実行で fail 確認**

```bash
pytest tests/test_config.py -v
```

期待値：FAIL（モジュール未作成）。

- [ ] **Step 3: 実装**

`nomiboy/src/nomiboy/config.py`:
```python
"""nomiboy 設定モジュール。

環境変数：
- NOMIBOY_FORCE_PI=1   ハード判定を強制的に Pi 扱い（再現テスト用）
- NOMIBOY_FULLSCREEN=0 全画面を無効化（PCデバッグ用）
"""
from __future__ import annotations

import os
from pathlib import Path

SCREEN_SIZE: tuple[int, int] = (480, 320)
TARGET_FPS: int = 30


def detect_is_pi() -> bool:
    if os.environ.get("NOMIBOY_FORCE_PI") == "1":
        return True
    model_file = Path("/sys/firmware/devicetree/base/model")
    if not model_file.exists():
        return False
    try:
        return "Raspberry Pi" in model_file.read_text(errors="ignore")
    except OSError:
        return False


def detect_fullscreen() -> bool:
    override = os.environ.get("NOMIBOY_FULLSCREEN")
    if override is not None:
        return override == "1"
    return detect_is_pi()


def detect_hide_cursor() -> bool:
    return detect_is_pi()


# モジュール読み込み時に1度だけ評価（テストでは関数を直接呼ぶ）
IS_PI = detect_is_pi()
FULLSCREEN = detect_fullscreen()
HIDE_CURSOR = detect_hide_cursor()

ROOT_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"
TTS_CACHE_DIR = ASSETS_DIR / "tts_cache"
LOG_DIR = Path.home() / ".nomiboy"
```

- [ ] **Step 4: テスト実行で pass 確認**

```bash
pytest tests/test_config.py -v
```

期待値：4 PASS。

- [ ] **Step 5: コミット**

```bash
git add nomiboy/src/nomiboy/config.py nomiboy/tests/test_config.py
git commit -m "nomiboy: Config モジュール（IS_PI 判定・画面サイズ・パス定義）"
```

---

## Task 5: Colors モジュール（GBC パレット）

**Files:**
- Create: `nomiboy/src/nomiboy/colors.py`

GBC 風のカラフルなパレットを定義。プレイヤー色割り当て用に4色プリセットを用意。

- [ ] **Step 1: 実装**（このモジュールは定数のみなので TDD ではなく直接定義）

`nomiboy/src/nomiboy/colors.py`:
```python
"""nomiboy GBC 風カラーパレット。

仮の値。最終的な配色は DESIGN.md（Task 27）で確定する。
"""
from __future__ import annotations

# 基本背景・前景
BG_PRIMARY: tuple[int, int, int] = (255, 203, 5)        # 黄
BG_SECONDARY: tuple[int, int, int] = (255, 119, 0)      # オレンジ
INK_DARK: tuple[int, int, int] = (43, 10, 61)           # 紫黒
INK_LIGHT: tuple[int, int, int] = (255, 255, 255)       # 白

# アクセント
ACCENT_BERRY: tuple[int, int, int] = (176, 48, 96)      # ベリー
ACCENT_LIME: tuple[int, int, int] = (155, 188, 15)      # DMG ライム

# プレイヤー4色（登録順にローテ割当）
PLAYER_COLORS: list[tuple[int, int, int]] = [
    (220, 60, 60),    # 赤
    (60, 130, 220),   # 青
    (60, 190, 90),    # 緑
    (240, 200, 50),   # 黄
]

# 警告
DANGER_RED: tuple[int, int, int] = (220, 30, 30)
WARNING_AMBER: tuple[int, int, int] = (240, 160, 0)


def player_color(index: int) -> tuple[int, int, int]:
    """プレイヤー番号（0始まり）から色を返す。4を超えたら循環。"""
    return PLAYER_COLORS[index % len(PLAYER_COLORS)]
```

- [ ] **Step 2: 簡単なテスト**（player_color の循環のみ）

`nomiboy/tests/test_colors.py`:
```python
from nomiboy.colors import PLAYER_COLORS, player_color


def test_player_color_returns_distinct_for_first_4():
    cs = [player_color(i) for i in range(4)]
    assert len(set(cs)) == 4


def test_player_color_wraps_around():
    assert player_color(0) == player_color(4)
```

- [ ] **Step 3: テスト実行**

```bash
pytest tests/test_colors.py -v
```

期待値：2 PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/colors.py nomiboy/tests/test_colors.py
git commit -m "nomiboy: 仮の GBC 風カラーパレットを追加"
```

---

# Phase 2: コアサービス（ロジック層）

## Task 6: PlayerStore + Player

**Files:**
- Create: `nomiboy/src/nomiboy/stores/player_store.py`
- Create: `nomiboy/tests/test_player_store.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
import pytest
from nomiboy.stores.player_store import PlayerStore, Player


def test_store_starts_empty():
    s = PlayerStore()
    assert s.players == []
    assert s.count == 0


def test_add_assigns_sequential_id():
    s = PlayerStore()
    s.add("たろう")
    s.add("はなこ")
    assert [p.id for p in s.players] == [0, 1]


def test_add_assigns_color_from_palette():
    s = PlayerStore()
    s.add("a")
    s.add("b")
    assert s.players[0].color != s.players[1].color


def test_max_4_players():
    s = PlayerStore()
    for n in "abcd":
        s.add(n)
    with pytest.raises(ValueError):
        s.add("e")


def test_can_start_requires_min_2():
    s = PlayerStore()
    s.add("a")
    assert not s.can_start()
    s.add("b")
    assert s.can_start()


def test_remove_by_index():
    s = PlayerStore()
    s.add("a"); s.add("b"); s.add("c")
    s.remove(1)
    assert [p.name for p in s.players] == ["a", "c"]


def test_clear():
    s = PlayerStore()
    s.add("a"); s.add("b")
    s.clear()
    assert s.players == []


def test_name_max_length_8():
    s = PlayerStore()
    with pytest.raises(ValueError):
        s.add("123456789")  # 9文字
```

- [ ] **Step 2: 実装**

`nomiboy/src/nomiboy/stores/player_store.py`:
```python
"""プレイヤー登録ストア。"""
from __future__ import annotations

from dataclasses import dataclass

from nomiboy.colors import player_color

MAX_PLAYERS = 4
MIN_PLAYERS_TO_START = 2
MAX_NAME_LEN = 8


@dataclass(frozen=True)
class Player:
    id: int
    name: str
    color: tuple[int, int, int]


class PlayerStore:
    def __init__(self) -> None:
        self._players: list[Player] = []
        self._next_id: int = 0

    @property
    def players(self) -> list[Player]:
        return list(self._players)

    @property
    def count(self) -> int:
        return len(self._players)

    def add(self, name: str) -> Player:
        if len(name) == 0 or len(name) > MAX_NAME_LEN:
            raise ValueError(f"name length must be 1-{MAX_NAME_LEN}")
        if len(self._players) >= MAX_PLAYERS:
            raise ValueError(f"max {MAX_PLAYERS} players")
        p = Player(id=self._next_id, name=name, color=player_color(len(self._players)))
        self._players.append(p)
        self._next_id += 1
        return p

    def remove(self, index: int) -> None:
        del self._players[index]

    def clear(self) -> None:
        self._players.clear()
        self._next_id = 0

    def can_start(self) -> bool:
        return len(self._players) >= MIN_PLAYERS_TO_START
```

- [ ] **Step 3: テスト実行で全 PASS 確認**

```bash
pytest tests/test_player_store.py -v
```

期待値：8 PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/stores/player_store.py nomiboy/tests/test_player_store.py
git commit -m "nomiboy: PlayerStore（最大4人・色自動割当）を実装"
```

---

## Task 7: Scene 抽象 + SceneManager

**Files:**
- Create: `nomiboy/src/nomiboy/core/scene.py`
- Create: `nomiboy/src/nomiboy/core/scene_manager.py`
- Create: `nomiboy/tests/test_scene_manager.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
from dataclasses import dataclass, field
import pygame
from nomiboy.core.scene import Scene
from nomiboy.core.scene_manager import SceneManager


@dataclass
class FakeScene:
    name: str
    enter_calls: list = field(default_factory=list)
    exit_calls: int = 0
    events: list = field(default_factory=list)
    updates: list = field(default_factory=list)
    draws: int = 0

    def on_enter(self, ctx):
        self.enter_calls.append(ctx)

    def on_exit(self):
        self.exit_calls += 1

    def handle_event(self, e):
        self.events.append(e)

    def update(self, dt):
        self.updates.append(dt)

    def draw(self, surf):
        self.draws += 1


def test_push_calls_on_enter():
    sm = SceneManager(ctx="ctx")
    s = FakeScene("a")
    sm.push(s)
    assert s.enter_calls == ["ctx"]
    assert sm.current is s


def test_push_calls_on_exit_for_previous():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.push(b)
    assert a.exit_calls == 1
    assert sm.current is b


def test_pop_returns_to_previous():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.push(b)
    sm.pop()
    assert sm.current is a
    assert b.exit_calls == 1


def test_replace_swaps_top():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.replace(b)
    assert sm.current is b
    assert a.exit_calls == 1
    assert sm.depth == 1


def test_reset_to_clears_stack():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b"); c = FakeScene("c")
    sm.push(a); sm.push(b); sm.reset_to(c)
    assert sm.current is c
    assert sm.depth == 1
    assert a.exit_calls == 1 and b.exit_calls == 1


def test_event_routes_to_top():
    sm = SceneManager(ctx="ctx")
    a = FakeScene("a"); b = FakeScene("b")
    sm.push(a); sm.push(b)
    sm.handle_event("e")
    assert b.events == ["e"]
    assert a.events == []
```

- [ ] **Step 2: 実装**

`nomiboy/src/nomiboy/core/scene.py`:
```python
"""Scene プロトコル。各画面はこれを満たす。"""
from __future__ import annotations

from typing import Protocol, Any

import pygame


class Scene(Protocol):
    def on_enter(self, ctx: Any) -> None: ...
    def on_exit(self) -> None: ...
    def handle_event(self, event: Any) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
```

`nomiboy/src/nomiboy/core/scene_manager.py`:
```python
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
        while self._stack:
            self._stack.pop().on_exit()
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
```

- [ ] **Step 3: テスト実行で PASS 確認**

```bash
pytest tests/test_scene_manager.py -v
```

期待値：6 PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/core/scene.py nomiboy/src/nomiboy/core/scene_manager.py nomiboy/tests/test_scene_manager.py
git commit -m "nomiboy: Scene Protocol と SceneManager（push/pop/replace/reset_to）"
```

---

## Task 8: InputAdapter（タッチ/マウス統一）

**Files:**
- Create: `nomiboy/src/nomiboy/core/input_adapter.py`
- Create: `nomiboy/tests/test_input_adapter.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
from types import SimpleNamespace
import pygame
from nomiboy.core.input_adapter import InputAdapter, InputEvent, InputKind


def test_mouse_button_down_becomes_tap():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, pos=(100, 50), button=1)
    out = ia.translate(pg_event)
    assert out == InputEvent(kind=InputKind.TAP, x=100, y=50)


def test_mouse_button_up_becomes_release():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEBUTTONUP, pos=(10, 20), button=1)
    out = ia.translate(pg_event)
    assert out.kind == InputKind.RELEASE


def test_mouse_motion_with_button_pressed_becomes_drag():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEMOTION, pos=(50, 60), buttons=(1, 0, 0))
    out = ia.translate(pg_event)
    assert out.kind == InputKind.DRAG


def test_mouse_motion_without_button_returns_none():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.MOUSEMOTION, pos=(50, 60), buttons=(0, 0, 0))
    out = ia.translate(pg_event)
    assert out is None


def test_finger_down_normalized_coords_scaled():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.FINGERDOWN, x=0.5, y=0.25)
    out = ia.translate(pg_event)
    assert out == InputEvent(kind=InputKind.TAP, x=240, y=80)


def test_unknown_event_returns_none():
    ia = InputAdapter(screen_size=(480, 320))
    pg_event = SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_a)
    assert ia.translate(pg_event) is None
```

- [ ] **Step 2: 実装**

`nomiboy/src/nomiboy/core/input_adapter.py`:
```python
"""タッチイベントとマウスイベントを統一の InputEvent に変換。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import pygame


class InputKind(Enum):
    TAP = "tap"
    RELEASE = "release"
    DRAG = "drag"


@dataclass(frozen=True)
class InputEvent:
    kind: InputKind
    x: int
    y: int


class InputAdapter:
    def __init__(self, screen_size: tuple[int, int]) -> None:
        self._w, self._h = screen_size

    def translate(self, event: Any) -> InputEvent | None:
        et = getattr(event, "type", None)
        if et == pygame.MOUSEBUTTONDOWN and getattr(event, "button", None) == 1:
            x, y = event.pos
            return InputEvent(InputKind.TAP, int(x), int(y))
        if et == pygame.MOUSEBUTTONUP and getattr(event, "button", None) == 1:
            x, y = event.pos
            return InputEvent(InputKind.RELEASE, int(x), int(y))
        if et == pygame.MOUSEMOTION:
            buttons = getattr(event, "buttons", (0, 0, 0))
            if buttons[0]:
                x, y = event.pos
                return InputEvent(InputKind.DRAG, int(x), int(y))
            return None
        if et == pygame.FINGERDOWN:
            return InputEvent(InputKind.TAP, int(event.x * self._w), int(event.y * self._h))
        if et == pygame.FINGERUP:
            return InputEvent(InputKind.RELEASE, int(event.x * self._w), int(event.y * self._h))
        if et == pygame.FINGERMOTION:
            return InputEvent(InputKind.DRAG, int(event.x * self._w), int(event.y * self._h))
        return None
```

- [ ] **Step 3: テスト実行**

```bash
pytest tests/test_input_adapter.py -v
```

期待値：6 PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/core/input_adapter.py nomiboy/tests/test_input_adapter.py
git commit -m "nomiboy: InputAdapter（マウス/タッチを InputEvent に統一）"
```

---

# Phase 3: コアサービス（IO 層）

## Task 9: AssetLoader

**Files:**
- Create: `nomiboy/src/nomiboy/core/asset_loader.py`

- [ ] **Step 1: 実装**（IO はテストせず、薄いラッパとして実装。テストはのちのウィジェットで間接的に通る）

```python
"""画像・フォントの読み込みとキャッシュ。"""
from __future__ import annotations

from pathlib import Path

import pygame

from nomiboy.config import ASSETS_DIR


class AssetLoader:
    def __init__(self, base_dir: Path = ASSETS_DIR) -> None:
        self._base = base_dir
        self._image_cache: dict[Path, pygame.Surface] = {}
        self._font_cache: dict[tuple[str, int], pygame.font.Font] = {}

    def image(self, relative_path: str) -> pygame.Surface:
        p = self._base / relative_path
        cached = self._image_cache.get(p)
        if cached is not None:
            return cached
        surf = pygame.image.load(str(p)).convert_alpha()
        self._image_cache[p] = surf
        return surf

    def font(self, name: str, size: int) -> pygame.font.Font:
        key = (name, size)
        cached = self._font_cache.get(key)
        if cached is not None:
            return cached
        font_path = self._base / "fonts" / name
        if font_path.exists():
            f = pygame.font.Font(str(font_path), size)
        else:
            f = pygame.font.Font(None, size)  # システムフォントフォールバック
        self._font_cache[key] = f
        return f
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/core/asset_loader.py
git commit -m "nomiboy: AssetLoader（画像・フォントのキャッシュ）"
```

---

## Task 10: AudioService

**Files:**
- Create: `nomiboy/src/nomiboy/core/audio_service.py`

- [ ] **Step 1: 実装**

```python
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
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def set_master_volume(self, v: float) -> None:
        self._master = max(0.0, min(1.0, v))
        pygame.mixer.music.set_volume(self._master)

    def play_se(self, name: str) -> None:
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
        path = self._base / "bgm" / name
        if not path.exists():
            return
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(self._master)
        pygame.mixer.music.play(-1 if loop else 0)

    def stop_bgm(self) -> None:
        pygame.mixer.music.stop()
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/core/audio_service.py
git commit -m "nomiboy: AudioService（BGM/SE 再生、ファイル欠損は黙ってスキップ）"
```

---

## Task 11: TTSService（Gemini + キャッシュ）

**Files:**
- Create: `nomiboy/src/nomiboy/core/tts_service.py`
- Create: `nomiboy/tests/test_tts_service.py`

**注意：** Gemini TTS の実 API 呼び出しはテストしない。キャッシュロジックと例外抑制のみテスト。

- [ ] **Step 1: 失敗するテストを書く**

```python
import pytest
from pathlib import Path
from nomiboy.core.tts_service import TTSService


def test_speak_returns_cached_path_when_exists(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    text = "こんにちは"
    # サービスがキー算出に使うのと同じ方法で事前にキャッシュを置く
    svc = TTSService(api_key=None, cache_dir=cache)
    key = svc.cache_key(text, voice="default")
    expected_path = cache / f"{key}.wav"
    expected_path.write_bytes(b"FAKE")
    assert svc.speak(text) == expected_path


def test_speak_returns_none_when_offline_and_no_cache(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    svc = TTSService(api_key=None, cache_dir=cache)
    assert svc.speak("uncached text") is None


def test_speak_swallows_exceptions(tmp_path, monkeypatch):
    cache = tmp_path / "cache"; cache.mkdir()
    svc = TTSService(api_key="dummy", cache_dir=cache)
    def boom(*a, **kw):
        raise RuntimeError("boom")
    monkeypatch.setattr(svc, "_synthesize", boom)
    assert svc.speak("anything") is None  # 例外は外に漏らさない
```

- [ ] **Step 2: 実装**

```python
"""Gemini TTS サービス。永続キャッシュ + 例外吸収。"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from nomiboy.config import TTS_CACHE_DIR

log = logging.getLogger(__name__)


class TTSService:
    def __init__(
        self,
        api_key: str | None,
        cache_dir: Path = TTS_CACHE_DIR,
        timeout_sec: float = 5.0,
    ) -> None:
        self._api_key = api_key
        self._cache_dir = cache_dir
        self._timeout = timeout_sec
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def cache_key(self, text: str, voice: str = "default") -> str:
        h = hashlib.sha1(f"{voice}|{text}".encode("utf-8")).hexdigest()
        return h[:16]

    def speak(self, text: str, voice: str = "default") -> Path | None:
        try:
            key = self.cache_key(text, voice)
            path = self._cache_dir / f"{key}.wav"
            if path.exists():
                return path
            if not self._api_key:
                return None
            wav_bytes = self._synthesize(text, voice)
            if wav_bytes is None:
                return None
            path.write_bytes(wav_bytes)
            return path
        except Exception as e:
            log.warning("TTS failed: %s", e)
            return None

    def _synthesize(self, text: str, voice: str) -> bytes | None:
        """実際の Gemini API 呼び出し。実装は Task 11b（後続）で詰める。"""
        # 最小実装：API 未対応なら None。
        # 実機接続テスト時に google-genai を使った合成を追加する。
        return None
```

- [ ] **Step 3: テスト実行**

```bash
pytest tests/test_tts_service.py -v
```

期待値：3 PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/core/tts_service.py nomiboy/tests/test_tts_service.py
git commit -m "nomiboy: TTSService の骨格（キャッシュ + 例外抑制、Gemini 合成は別途）"
```

**注：実 Gemini API 連携は MVP 統合フェーズ（Task 24 以降の動作確認時）に追加する。** spec 12 章「後で詰める」に記載済み。

---

# Phase 4: ウィジェット

## Task 12: Text widget

**Files:**
- Create: `nomiboy/src/nomiboy/core/widgets/text.py`

- [ ] **Step 1: 実装**

```python
"""テキスト描画ヘルパ。フォントサーフェスをキャッシュ。"""
from __future__ import annotations

import pygame


class TextRenderer:
    def __init__(self, font: pygame.font.Font, color: tuple[int, int, int]) -> None:
        self._font = font
        self._color = color
        self._cache: dict[tuple[str, tuple[int, int, int]], pygame.Surface] = {}

    def render(self, text: str, color: tuple[int, int, int] | None = None) -> pygame.Surface:
        c = color or self._color
        key = (text, c)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        surf = self._font.render(text, True, c)
        self._cache[key] = surf
        return surf

    def draw(
        self,
        surface: pygame.Surface,
        text: str,
        pos: tuple[int, int],
        anchor: str = "topleft",
        color: tuple[int, int, int] | None = None,
    ) -> pygame.Rect:
        s = self.render(text, color)
        rect = s.get_rect(**{anchor: pos})
        surface.blit(s, rect)
        return rect
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/core/widgets/text.py
git commit -m "nomiboy: TextRenderer（フォントサーフェスキャッシュ）"
```

---

## Task 13: Button widget

**Files:**
- Create: `nomiboy/src/nomiboy/core/widgets/button.py`

- [ ] **Step 1: 実装**

```python
"""タッチ可能なボタン。InputEvent.TAP の hit-test を提供。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.text import TextRenderer


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    on_tap: Callable[[], None]
    bg_color: tuple[int, int, int] = (255, 203, 5)
    fg_color: tuple[int, int, int] = (43, 10, 61)
    border_color: tuple[int, int, int] = (43, 10, 61)
    enabled: bool = True

    def hit(self, event: InputEvent) -> bool:
        if not self.enabled:
            return False
        if event.kind != InputKind.TAP:
            return False
        return self.rect.collidepoint(event.x, event.y)

    def handle(self, event: InputEvent) -> bool:
        if self.hit(event):
            self.on_tap()
            return True
        return False

    def draw(self, surface: pygame.Surface, text_renderer: TextRenderer) -> None:
        color = self.bg_color if self.enabled else (160, 160, 160)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, width=2)
        text_renderer.draw(surface, self.label, self.rect.center, anchor="center", color=self.fg_color)
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/core/widgets/button.py
git commit -m "nomiboy: Button ウィジェット（タッチで on_tap）"
```

---

## Task 14: Keyboard widget（50音/カナ/英数字）

**Files:**
- Create: `nomiboy/src/nomiboy/core/widgets/keyboard.py`
- Create: `nomiboy/tests/test_keyboard_widget.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
from nomiboy.core.widgets.keyboard import VirtualKeyboard, KeyboardMode


def test_starts_in_hiragana_mode():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    assert kb.mode == KeyboardMode.HIRAGANA


def test_switch_mode_cycles():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.switch_mode()
    assert kb.mode == KeyboardMode.KATAKANA
    kb.switch_mode()
    assert kb.mode == KeyboardMode.ALPHANUM
    kb.switch_mode()
    assert kb.mode == KeyboardMode.HIRAGANA


def test_append_character_capped_at_max():
    kb = VirtualKeyboard(area=(0, 60, 480, 260), max_len=3)
    kb.text = "あい"
    kb.append("う")
    kb.append("え")  # 4文字目は無視
    assert kb.text == "あいう"


def test_backspace_removes_last_char():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.text = "あいう"
    kb.backspace()
    assert kb.text == "あい"


def test_clear_resets_text():
    kb = VirtualKeyboard(area=(0, 60, 480, 260))
    kb.text = "abc"
    kb.clear()
    assert kb.text == ""
```

- [ ] **Step 2: 実装**

```python
"""仮想キーボード。50音/カナ/英数字をタブで切替。"""
from __future__ import annotations

from enum import Enum

HIRAGANA_ROWS = [
    "あいうえお",
    "かきくけこ",
    "さしすせそ",
    "たちつてと",
    "なにぬねの",
    "はひふへほ",
    "まみむめも",
    "やゆよわん",
    "らりるれろ",
    "がぎぐげご",
    "ざじずぜぞ",
    "だぢづでど",
    "ばびぶべぼ",
    "ぱぴぷぺぽ",
]

KATAKANA_ROWS = [
    "アイウエオ",
    "カキクケコ",
    "サシスセソ",
    "タチツテト",
    "ナニヌネノ",
    "ハヒフヘホ",
    "マミムメモ",
    "ヤユヨワン",
    "ラリルレロ",
    "ガギグゲゴ",
    "ザジズゼゾ",
    "ダヂヅデド",
    "バビブベボ",
    "パピプペポ",
]

ALPHANUM_ROWS = [
    "1234567890",
    "abcdefghij",
    "klmnopqrst",
    "uvwxyz",
]


class KeyboardMode(Enum):
    HIRAGANA = "hira"
    KATAKANA = "kata"
    ALPHANUM = "alnum"


class VirtualKeyboard:
    def __init__(self, area: tuple[int, int, int, int], max_len: int = 8) -> None:
        self.area = area  # x, y, w, h
        self.max_len = max_len
        self.text: str = ""
        self.mode: KeyboardMode = KeyboardMode.HIRAGANA

    def rows(self) -> list[str]:
        if self.mode == KeyboardMode.HIRAGANA:
            return HIRAGANA_ROWS
        if self.mode == KeyboardMode.KATAKANA:
            return KATAKANA_ROWS
        return ALPHANUM_ROWS

    def switch_mode(self) -> None:
        order = [KeyboardMode.HIRAGANA, KeyboardMode.KATAKANA, KeyboardMode.ALPHANUM]
        self.mode = order[(order.index(self.mode) + 1) % len(order)]

    def append(self, ch: str) -> None:
        if len(self.text) >= self.max_len:
            return
        self.text += ch

    def backspace(self) -> None:
        self.text = self.text[:-1]

    def clear(self) -> None:
        self.text = ""

    # 描画とヒット判定は Scene 側で行う（行・列のグリッドを area 内で計算）。
    # ここではテキストバッファとモード管理だけを責務にする。
```

- [ ] **Step 3: テスト実行**

```bash
pytest tests/test_keyboard_widget.py -v
```

期待値：5 PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/core/widgets/keyboard.py nomiboy/tests/test_keyboard_widget.py
git commit -m "nomiboy: VirtualKeyboard（50音/カナ/英数字、最大8文字）"
```

---

# Phase 5: アプリ骨格

## Task 15: AppContext + main.py + メインループ

**Files:**
- Create: `nomiboy/src/nomiboy/app.py`
- Create: `nomiboy/src/nomiboy/main.py`

- [ ] **Step 1: AppContext と App クラスを実装**

`nomiboy/src/nomiboy/app.py`:
```python
"""nomiboy の起動とメインループ。AppContext を保持して各 Scene に渡す。"""
from __future__ import annotations

import logging
import os
import socket
import sys
from dataclasses import dataclass
from typing import Optional

import pygame

from nomiboy import config
from nomiboy.colors import BG_PRIMARY, DANGER_RED, INK_DARK
from nomiboy.core.asset_loader import AssetLoader
from nomiboy.core.audio_service import AudioService
from nomiboy.core.input_adapter import InputAdapter
from nomiboy.core.scene_manager import SceneManager
from nomiboy.core.tts_service import TTSService
from nomiboy.core.widgets.text import TextRenderer
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
        self.sm.reset_to(self._title_scene())

    def _title_scene(self):
        from nomiboy.scenes.title import TitleScene
        return TitleScene(self.sm)
```

- [ ] **Step 2: エントリーポイント `main.py` を実装**

`nomiboy/src/nomiboy/main.py`:
```python
"""python -m nomiboy のエントリーポイント。"""
from __future__ import annotations

import argparse
import logging
import os
import sys

from nomiboy.app import App
from nomiboy.config import LOG_DIR


def _setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "log.txt"),
            logging.StreamHandler(sys.stderr),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--windowed", action="store_true", help="全画面を無効化（PCデバッグ用）")
    args = parser.parse_args()
    if args.windowed:
        os.environ["NOMIBOY_FULLSCREEN"] = "0"
    _setup_logging()
    App().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: `python -m nomiboy.main` で起動するように `__init__.py` 更新（不要）**

確認：`python -m nomiboy --windowed` が動くこと。Title Scene 未作成のため `ImportError` が出る。Task 16 で修正。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/app.py nomiboy/src/nomiboy/main.py
git commit -m "nomiboy: AppContext・メインループ・例外フェイルセーフ・WiFi検出"
```

---

# Phase 6: ベースシーン

## Task 16: TitleScene

**Files:**
- Create: `nomiboy/src/nomiboy/scenes/title.py`

- [ ] **Step 1: 実装**

```python
"""タイトル画面。tap で PlayerRegisterScene へ。"""
from __future__ import annotations

import time

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.text import TextRenderer


class TitleScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._title_renderer: TextRenderer | None = None
        self._sub_renderer: TextRenderer | None = None
        self._offline_renderer: TextRenderer | None = None
        self._t0 = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_renderer = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 36), colors.INK_DARK)
        self._sub_renderer = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 14), colors.INK_DARK)
        self._offline_renderer = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 10), colors.DANGER_RED)
        self._t0 = time.time()

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        if event.kind == InputKind.TAP:
            from nomiboy.scenes.player_register import PlayerRegisterScene
            self._sm.replace(PlayerRegisterScene(self._sm))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_renderer.draw(surface, "NOMIBOY", (config.SCREEN_SIZE[0] // 2, 130), anchor="center")
        # 点滅
        if int((time.time() - self._t0) * 2) % 2 == 0:
            self._sub_renderer.draw(surface, "TAP TO START", (config.SCREEN_SIZE[0] // 2, 220), anchor="center")
        if not self._ctx.online:
            self._offline_renderer.draw(surface, "OFFLINE", (config.SCREEN_SIZE[0] - 8, 8), anchor="topright")
```

- [ ] **Step 2: PCで動作確認**

```bash
cd nomiboy && source venv/bin/activate
PYTHONPATH=src python -m nomiboy --windowed
```

期待値：480×320 ウィンドウが開き、黄色背景に「NOMIBOY」「TAP TO START」が表示される。クリックすると PlayerRegisterScene 未実装でエラー → Task 17 で対応。

- [ ] **Step 3: コミット**

```bash
git add nomiboy/src/nomiboy/scenes/title.py
git commit -m "nomiboy: TitleScene（NOMIBOY ロゴ・点滅・オフライン警告）"
```

---

## Task 17: PlayerRegisterScene

**Files:**
- Create: `nomiboy/src/nomiboy/scenes/player_register.py`

- [ ] **Step 1: 実装**

```python
"""プレイヤー登録画面。最大4人まで追加・削除、≥2人で開始可能。"""
from __future__ import annotations

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class PlayerRegisterScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._buttons: list[Button] = []
        self._title_r: TextRenderer | None = None
        self._name_r: TextRenderer | None = None

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._name_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 14), colors.INK_DARK)
        self._rebuild_buttons()

    def on_exit(self) -> None:
        pass

    def _rebuild_buttons(self) -> None:
        self._buttons = []
        # 「+追加」ボタン（プレイヤー数 < 4 のときのみ）
        if self._ctx.players.count < 4:
            self._buttons.append(Button(
                rect=pygame.Rect(20, 250, 140, 50),
                label="+ ADD",
                on_tap=self._open_keyboard,
                bg_color=colors.ACCENT_LIME,
            ))
        # 「開始」ボタン
        self._buttons.append(Button(
            rect=pygame.Rect(320, 250, 140, 50),
            label="START",
            on_tap=self._start,
            bg_color=colors.BG_SECONDARY,
            enabled=self._ctx.players.can_start(),
        ))
        # 各プレイヤーの削除ボタン
        for i, p in enumerate(self._ctx.players.players):
            self._buttons.append(Button(
                rect=pygame.Rect(360, 60 + i * 40, 100, 30),
                label="REMOVE",
                on_tap=lambda idx=i: self._remove(idx),
                bg_color=colors.DANGER_RED,
                fg_color=colors.INK_LIGHT,
            ))

    def _open_keyboard(self) -> None:
        from nomiboy.scenes.keyboard_input import KeyboardInputScene
        self._sm.push(KeyboardInputScene(self._sm, on_confirm=self._on_name_confirmed))

    def _on_name_confirmed(self, name: str) -> None:
        try:
            self._ctx.players.add(name)
        except ValueError:
            pass
        self._rebuild_buttons()

    def _remove(self, idx: int) -> None:
        self._ctx.players.remove(idx)
        self._rebuild_buttons()

    def _start(self) -> None:
        if not self._ctx.players.can_start():
            return
        from nomiboy.scenes.game_select import GameSelectScene
        self._sm.replace(GameSelectScene(self._sm))

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_r.draw(surface, f"PLAYERS  {self._ctx.players.count}/4", (config.SCREEN_SIZE[0] // 2, 30), anchor="center")
        for i, p in enumerate(self._ctx.players.players):
            pygame.draw.circle(surface, p.color, (40, 75 + i * 40), 12)
            self._name_r.draw(surface, p.name, (70, 75 + i * 40), anchor="midleft")
        for b in self._buttons:
            b.draw(surface, self._name_r)
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/scenes/player_register.py
git commit -m "nomiboy: PlayerRegisterScene（追加/削除/開始ボタン）"
```

---

## Task 18: KeyboardInputScene

**Files:**
- Create: `nomiboy/src/nomiboy/scenes/keyboard_input.py`

- [ ] **Step 1: 実装**

```python
"""仮想キーボード画面。確定で前画面に戻り、コールバックで名前を渡す。"""
from __future__ import annotations

from typing import Callable

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.keyboard import KeyboardMode, VirtualKeyboard
from nomiboy.core.widgets.text import TextRenderer


class KeyboardInputScene:
    def __init__(self, scene_manager, on_confirm: Callable[[str], None]) -> None:
        self._sm = scene_manager
        self._on_confirm = on_confirm
        self._ctx: AppContext | None = None
        self._kb = VirtualKeyboard(area=(10, 80, 460, 200), max_len=8)
        self._buttons: list[Button] = []
        self._char_rects: list[tuple[pygame.Rect, str]] = []
        self._text_r: TextRenderer | None = None
        self._char_r: TextRenderer | None = None

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._text_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._char_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 14), colors.INK_DARK)
        self._buttons = [
            Button(pygame.Rect(10, 290, 100, 24), "MODE", self._kb.switch_mode, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(120, 290, 80, 24), "BS", self._kb.backspace, bg_color=colors.WARNING_AMBER),
            Button(pygame.Rect(210, 290, 80, 24), "CLR", self._kb.clear, bg_color=colors.WARNING_AMBER),
            Button(pygame.Rect(370, 290, 100, 24), "OK", self._confirm, bg_color=colors.BG_SECONDARY),
            Button(pygame.Rect(10, 10, 60, 24), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
        ]
        self._build_grid()

    def on_exit(self) -> None:
        pass

    def _build_grid(self) -> None:
        self._char_rects = []
        x0, y0, w, h = self._kb.area
        rows = self._kb.rows()
        rh = h // max(1, len(rows))
        for ri, row in enumerate(rows):
            cw = w // max(1, len(row))
            for ci, ch in enumerate(row):
                r = pygame.Rect(x0 + ci * cw, y0 + ri * rh, cw - 2, rh - 2)
                self._char_rects.append((r, ch))

    def _confirm(self) -> None:
        if not self._kb.text:
            return
        self._on_confirm(self._kb.text)
        self._sm.pop()

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                if b.label == "MODE":
                    self._build_grid()
                return
        if event.kind == InputKind.TAP:
            for r, ch in self._char_rects:
                if r.collidepoint(event.x, event.y):
                    self._kb.append(ch)
                    return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._text_r.draw(surface, self._kb.text or "_", (config.SCREEN_SIZE[0] // 2, 50), anchor="center")
        for r, ch in self._char_rects:
            pygame.draw.rect(surface, colors.INK_LIGHT, r)
            pygame.draw.rect(surface, colors.INK_DARK, r, width=1)
            self._char_r.draw(surface, ch, r.center, anchor="center")
        for b in self._buttons:
            b.draw(surface, self._char_r)
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/scenes/keyboard_input.py
git commit -m "nomiboy: KeyboardInputScene（50音/カナ/英数字グリッド）"
```

---

## Task 19: GameSelectScene

**Files:**
- Create: `nomiboy/src/nomiboy/scenes/game_select.py`

- [ ] **Step 1: 実装**（GameMeta は Task 21 で定義済みの想定だが、本タスクで先に最小定義）

`nomiboy/src/nomiboy/scenes/game_select.py`:
```python
"""ゲーム選択画面。`games/__init__.py` の GAME_META 一覧を表示。"""
from __future__ import annotations

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.games import GAME_META


class GameSelectScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._buttons: list[Button] = []
        self._title_r: TextRenderer | None = None
        self._btn_r: TextRenderer | None = None
        self._ctx: AppContext | None = None

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._btn_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 12), colors.INK_DARK)
        self._buttons = []
        # ゲーム3つ横並び
        bw, bh = 130, 130
        gap = (config.SCREEN_SIZE[0] - bw * 3) // 4
        y = 90
        for i, meta in enumerate(GAME_META):
            x = gap + i * (bw + gap)
            self._buttons.append(Button(
                rect=pygame.Rect(x, y, bw, bh),
                label=meta.title,
                on_tap=lambda key=meta.key: self._launch(key),
                bg_color=colors.player_color(i),
            ))
        # タイトルへ戻る
        self._buttons.append(Button(
            rect=pygame.Rect(10, 10, 100, 26),
            label="TITLE",
            on_tap=self._reset_to_title,
            bg_color=colors.ACCENT_BERRY,
            fg_color=colors.INK_LIGHT,
        ))

    def on_exit(self) -> None:
        pass

    def _launch(self, key: str) -> None:
        if key == "bomb":
            from nomiboy.games.bomb import BombScene
            self._sm.push(BombScene(self._sm))
        elif key == "roulette":
            from nomiboy.games.roulette import RouletteScene
            self._sm.push(RouletteScene(self._sm))
        elif key == "odai":
            from nomiboy.games.odai import OdaiScene
            self._sm.push(OdaiScene(self._sm))

    def _reset_to_title(self) -> None:
        from nomiboy.scenes.title import TitleScene
        self._ctx.players.clear()
        self._sm.reset_to(TitleScene(self._sm))

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_r.draw(surface, "SELECT GAME", (config.SCREEN_SIZE[0] // 2, 50), anchor="center")
        for b in self._buttons:
            b.draw(surface, self._btn_r)
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/scenes/game_select.py
git commit -m "nomiboy: GameSelectScene（GAME_META 一覧から横並びボタン）"
```

---

## Task 20: ResultScene

**Files:**
- Create: `nomiboy/src/nomiboy/scenes/result.py`

- [ ] **Step 1: 実装**

```python
"""結果発表画面。爆弾・ルーレットでハズレた人を表示。"""
from __future__ import annotations

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.text import TextRenderer
from nomiboy.stores.player_store import Player


class ResultScene:
    def __init__(self, scene_manager, loser: Player) -> None:
        self._sm = scene_manager
        self._loser = loser
        self._title_r: TextRenderer | None = None
        self._sub_r: TextRenderer | None = None

    def on_enter(self, ctx: AppContext) -> None:
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 28), colors.INK_DARK)
        self._sub_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 12), colors.INK_DARK)
        # TTS で読み上げ（オフライン時は何もしない）
        if ctx.online:
            ctx.tts.speak(f"{self._loser.name} は飲む！")

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        if event.kind == InputKind.TAP:
            # ゲーム選択へ戻る（Bomb/Roulette → Result の上に GameSelect が居る想定）
            self._sm.pop()  # Result 抜ける
            self._sm.pop()  # 個別ゲームも抜ける（GameSelect に戻る）

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(self._loser.color)
        self._title_r.draw(surface, f"{self._loser.name}", (config.SCREEN_SIZE[0] // 2, 120), anchor="center", color=colors.INK_LIGHT)
        self._sub_r.draw(surface, "は 飲む！", (config.SCREEN_SIZE[0] // 2, 170), anchor="center", color=colors.INK_LIGHT)
        self._sub_r.draw(surface, "tap to continue", (config.SCREEN_SIZE[0] // 2, 280), anchor="center", color=colors.INK_LIGHT)
```

- [ ] **Step 2: コミット**

```bash
git add nomiboy/src/nomiboy/scenes/result.py
git commit -m "nomiboy: ResultScene（ハズレ発表 + TTS 読み上げ）"
```

---

# Phase 7: ゲーム実装

## Task 21: GameMeta + BombScene

**Files:**
- Modify: `nomiboy/src/nomiboy/games/__init__.py`
- Create: `nomiboy/src/nomiboy/games/bomb.py`
- Create: `nomiboy/tests/games/test_bomb.py`

- [ ] **Step 1: GameMeta を `games/__init__.py` に定義**

```python
"""nomiboy ゲーム一覧。GameSelectScene が参照する。"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GameMeta:
    key: str
    title: str
    icon: str
    min_players: int
    max_players: int


GAME_META: list[GameMeta] = [
    GameMeta(key="bomb", title="BOMB", icon="bomb.png", min_players=2, max_players=4),
    GameMeta(key="roulette", title="ROULETTE", icon="roulette.png", min_players=2, max_players=4),
    GameMeta(key="odai", title="ODAI", icon="odai.png", min_players=2, max_players=4),
]
```

- [ ] **Step 2: BombScene のロジックを TDD**

`nomiboy/tests/games/test_bomb.py`:
```python
import random
from nomiboy.games.bomb import BombController


def test_timer_starts_within_range():
    rng = random.Random(0)
    c = BombController(player_count=3, rng=rng, min_sec=10, max_sec=30)
    c.start()
    assert 10.0 <= c.remaining <= 30.0


def test_pass_advances_holder():
    c = BombController(player_count=3)
    c.start()
    assert c.holder == 0
    c.pass_to_next()
    assert c.holder == 1
    c.pass_to_next(); c.pass_to_next()
    assert c.holder == 1  # 0→1→2→0→1


def test_tick_decreases_remaining():
    c = BombController(player_count=2)
    c.start()
    initial = c.remaining
    c.tick(0.5)
    assert c.remaining == initial - 0.5


def test_explodes_when_remaining_zero():
    c = BombController(player_count=2)
    c.start()
    c._remaining = 0.0
    assert c.exploded is True


def test_holder_at_explosion():
    c = BombController(player_count=2)
    c.start()
    c.pass_to_next()
    c._remaining = 0.0
    assert c.exploded is True
    assert c.holder == 1
```

- [ ] **Step 3: 実装**

`nomiboy/src/nomiboy/games/bomb.py`:
```python
"""爆弾タイマーゲーム。コントローラ（純ロジック）と Scene を分離。"""
from __future__ import annotations

import random
import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class BombController:
    def __init__(
        self,
        player_count: int,
        rng: random.Random | None = None,
        min_sec: float = 10.0,
        max_sec: float = 30.0,
    ) -> None:
        self._n = player_count
        self._rng = rng or random.Random()
        self._min = min_sec
        self._max = max_sec
        self._remaining: float = 0.0
        self._holder: int = 0
        self._started: bool = False

    @property
    def remaining(self) -> float:
        return self._remaining

    @property
    def holder(self) -> int:
        return self._holder

    @property
    def exploded(self) -> bool:
        return self._started and self._remaining <= 0.0

    def start(self) -> None:
        self._remaining = self._rng.uniform(self._min, self._max)
        self._holder = 0
        self._started = True

    def pass_to_next(self) -> None:
        if not self._started or self.exploded:
            return
        self._holder = (self._holder + 1) % self._n


    def tick(self, dt: float) -> None:
        if not self._started or self.exploded:
            return
        self._remaining = max(0.0, self._remaining - dt)


class BombScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._ctrl: BombController | None = None
        self._title_r: TextRenderer | None = None
        self._buttons: list[Button] = []

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._ctrl = BombController(player_count=ctx.players.count)
        self._ctrl.start()
        self._buttons = [
            Button(pygame.Rect(10, 10, 80, 26), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(160, 240, 160, 60), "PASS", self._ctrl.pass_to_next, bg_color=colors.BG_SECONDARY),
        ]

    def on_exit(self) -> None:
        pass

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        self._ctrl.tick(dt)
        if self._ctrl.exploded:
            from nomiboy.scenes.result import ResultScene
            loser = self._ctx.players.players[self._ctrl.holder]
            self._sm.push(ResultScene(self._sm, loser))

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        holder_player = self._ctx.players.players[self._ctrl.holder]
        self._title_r.draw(surface, f"BOMB: {holder_player.name}", (config.SCREEN_SIZE[0] // 2, 90), anchor="center")
        self._title_r.draw(surface, f"{self._ctrl.remaining:.1f}s", (config.SCREEN_SIZE[0] // 2, 160), anchor="center", color=colors.DANGER_RED)
        for b in self._buttons:
            b.draw(surface, self._title_r)
```

- [ ] **Step 4: テスト実行**

```bash
pytest tests/games/test_bomb.py -v
```

期待値：5 PASS。

- [ ] **Step 5: コミット**

```bash
git add nomiboy/src/nomiboy/games/__init__.py nomiboy/src/nomiboy/games/bomb.py nomiboy/tests/games/test_bomb.py
git commit -m "nomiboy: BombScene + BombController（TDD で爆発ロジック検証済）"
```

---

## Task 22: RouletteScene

**Files:**
- Create: `nomiboy/src/nomiboy/games/roulette.py`
- Create: `nomiboy/tests/games/test_roulette.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
import random
from nomiboy.games.roulette import RouletteController


def test_initial_state_spinning():
    c = RouletteController(player_count=3)
    c.start()
    assert c.is_spinning is True


def test_stop_picks_one():
    rng = random.Random(0)
    c = RouletteController(player_count=4, rng=rng)
    c.start()
    c.stop()
    assert c.is_spinning is False
    assert 0 <= c.selected_index < 4


def test_pick_is_uniform_enough():
    rng = random.Random(0)
    counts = [0, 0, 0, 0]
    for _ in range(1000):
        c = RouletteController(player_count=4, rng=rng)
        c.start(); c.stop()
        counts[c.selected_index] += 1
    # 各 250±100 程度
    assert all(150 < c < 350 for c in counts)
```

- [ ] **Step 2: 実装**

```python
"""ルーレットゲーム。"""
from __future__ import annotations

import random
import time

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent, InputKind
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer


class RouletteController:
    def __init__(self, player_count: int, rng: random.Random | None = None) -> None:
        self._n = player_count
        self._rng = rng or random.Random()
        self._spinning = False
        self._selected: int = 0
        self._cursor: int = 0  # 演出用カーソル位置

    @property
    def is_spinning(self) -> bool:
        return self._spinning

    @property
    def selected_index(self) -> int:
        return self._selected

    @property
    def cursor(self) -> int:
        return self._cursor

    def start(self) -> None:
        self._spinning = True
        self._cursor = 0

    def advance_cursor(self) -> None:
        if self._spinning:
            self._cursor = (self._cursor + 1) % self._n

    def stop(self) -> None:
        if not self._spinning:
            return
        self._selected = self._rng.randrange(self._n)
        self._cursor = self._selected
        self._spinning = False


class RouletteScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._ctrl: RouletteController | None = None
        self._title_r: TextRenderer | None = None
        self._buttons: list[Button] = []
        self._next_tick: float = 0.0

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._ctrl = RouletteController(player_count=ctx.players.count)
        self._ctrl.start()
        self._buttons = [
            Button(pygame.Rect(10, 10, 80, 26), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(160, 240, 160, 60), "STOP", self._stop, bg_color=colors.BG_SECONDARY),
        ]

    def on_exit(self) -> None:
        pass

    def _stop(self) -> None:
        self._ctrl.stop()
        from nomiboy.scenes.result import ResultScene
        loser = self._ctx.players.players[self._ctrl.selected_index]
        self._sm.push(ResultScene(self._sm, loser))

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        if not self._ctrl.is_spinning:
            return
        self._next_tick -= dt
        if self._next_tick <= 0:
            self._ctrl.advance_cursor()
            self._next_tick = 0.1  # 100ms ごとにカーソル進行

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        for i, p in enumerate(self._ctx.players.players):
            highlight = (i == self._ctrl.cursor)
            color = p.color if highlight else colors.INK_LIGHT
            rect = pygame.Rect(40 + i * 100, 100, 80, 80)
            pygame.draw.rect(surface, color, rect)
            self._title_r.draw(surface, p.name, rect.center, anchor="center", color=colors.INK_DARK)
        for b in self._buttons:
            b.draw(surface, self._title_r)
```

- [ ] **Step 3: テスト実行**

```bash
pytest tests/games/test_roulette.py -v
```

期待値：3 PASS。

- [ ] **Step 4: コミット**

```bash
git add nomiboy/src/nomiboy/games/roulette.py nomiboy/tests/games/test_roulette.py
git commit -m "nomiboy: RouletteScene + RouletteController（一様抽選を統計テスト）"
```

---

## Task 23: OdaiScene + odai_cards.json

**Files:**
- Create: `nomiboy/data/odai_cards.json`
- Create: `nomiboy/src/nomiboy/games/odai.py`
- Create: `nomiboy/tests/games/test_odai.py`

- [ ] **Step 1: お題データを作成**

`nomiboy/data/odai_cards.json`:
```json
[
  {"id": "01", "text": "最近一番遅くまで起きていた人"},
  {"id": "02", "text": "今日一番おしゃれな人"},
  {"id": "03", "text": "最後にトイレに行った人"},
  {"id": "04", "text": "今月誕生日が一番近い人"},
  {"id": "05", "text": "今日一番たくさん食べた人"},
  {"id": "06", "text": "スマホの充電が一番少ない人"},
  {"id": "07", "text": "髪が一番長い人"},
  {"id": "08", "text": "メガネをかけている人"},
  {"id": "09", "text": "今日笑った回数が一番多そうな人"},
  {"id": "10", "text": "明日が休みじゃない人"},
  {"id": "11", "text": "ペットを飼っている人"},
  {"id": "12", "text": "今日一番早起きだった人"},
  {"id": "13", "text": "最近恋をしている人"},
  {"id": "14", "text": "車で来た人"},
  {"id": "15", "text": "誕生日が4月の人"},
  {"id": "16", "text": "兄弟が3人以上いる人"},
  {"id": "17", "text": "今日財布を忘れそうになった人"},
  {"id": "18", "text": "去年より体重が増えた人"},
  {"id": "19", "text": "今着ている服が一番高そうな人"},
  {"id": "20", "text": "辛いものが食べられない人"},
  {"id": "21", "text": "黒い靴下を履いている人"},
  {"id": "22", "text": "好きな漫画が10個以上ある人"},
  {"id": "23", "text": "今日コーヒーを飲んだ人"},
  {"id": "24", "text": "電車通勤の人"},
  {"id": "25", "text": "中学校の校歌を歌える人"},
  {"id": "26", "text": "右利きじゃない人"},
  {"id": "27", "text": "今月、推しに会いに行った人"},
  {"id": "28", "text": "今日この中で一番眠そうな人"},
  {"id": "29", "text": "海外に1ヶ月以上住んだことがある人"},
  {"id": "30", "text": "明日筋肉痛になりそうな人"}
]
```

- [ ] **Step 2: 失敗するテストを書く**

`nomiboy/tests/games/test_odai.py`:
```python
import json
import random
from pathlib import Path

from nomiboy.games.odai import OdaiController, OdaiCard


def make_cards(n=10):
    return [OdaiCard(id=str(i), text=f"text{i}") for i in range(n)]


def test_pick_returns_card():
    rng = random.Random(0)
    c = OdaiController(cards=make_cards(5), rng=rng)
    card = c.next_card()
    assert card.text.startswith("text")


def test_recent_n_excluded():
    rng = random.Random(0)
    cards = make_cards(5)
    c = OdaiController(cards=cards, rng=rng, recent_window=3)
    seen = []
    for _ in range(8):
        seen.append(c.next_card().id)
    # 任意の3連続で重複なし
    for i in range(len(seen) - 2):
        assert len(set(seen[i:i + 3])) == 3


def test_load_from_json(tmp_path):
    path = tmp_path / "o.json"
    path.write_text(json.dumps([{"id": "1", "text": "a"}]), encoding="utf-8")
    cards = OdaiController.load_cards(path)
    assert cards == [OdaiCard(id="1", text="a")]


def test_load_falls_back_when_missing(tmp_path):
    cards = OdaiController.load_cards(tmp_path / "missing.json")
    assert len(cards) >= 5  # フォールバック5枚
```

- [ ] **Step 3: 実装**

```python
"""お題ゲーム（○○な人は飲む）。"""
from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from nomiboy import colors, config
from nomiboy.app import AppContext
from nomiboy.core.input_adapter import InputEvent
from nomiboy.core.widgets.button import Button
from nomiboy.core.widgets.text import TextRenderer

log = logging.getLogger(__name__)


FALLBACK_CARDS = [
    {"id": "f1", "text": "今日一番元気な人"},
    {"id": "f2", "text": "最近一番遅く寝た人"},
    {"id": "f3", "text": "今月誕生日が一番近い人"},
    {"id": "f4", "text": "メガネをかけている人"},
    {"id": "f5", "text": "今日コーヒーを飲んだ人"},
]


@dataclass(frozen=True)
class OdaiCard:
    id: str
    text: str


class OdaiController:
    def __init__(
        self,
        cards: list[OdaiCard],
        rng: random.Random | None = None,
        recent_window: int = 3,
    ) -> None:
        self._cards = cards
        self._rng = rng or random.Random()
        self._recent: list[str] = []
        self._window = recent_window

    @staticmethod
    def load_cards(path: Path) -> list[OdaiCard]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [OdaiCard(id=d["id"], text=d["text"]) for d in data]
        except (OSError, ValueError, KeyError) as e:
            log.warning("odai_cards.json load failed (%s), using fallback", e)
            return [OdaiCard(id=d["id"], text=d["text"]) for d in FALLBACK_CARDS]

    def next_card(self) -> OdaiCard:
        candidates = [c for c in self._cards if c.id not in self._recent] or self._cards
        card = self._rng.choice(candidates)
        self._recent.append(card.id)
        if len(self._recent) > self._window:
            self._recent.pop(0)
        return card


class OdaiScene:
    def __init__(self, scene_manager) -> None:
        self._sm = scene_manager
        self._ctx: AppContext | None = None
        self._ctrl: OdaiController | None = None
        self._current: OdaiCard | None = None
        self._title_r: TextRenderer | None = None
        self._body_r: TextRenderer | None = None
        self._buttons: list[Button] = []

    def on_enter(self, ctx: AppContext) -> None:
        self._ctx = ctx
        cards = OdaiController.load_cards(config.DATA_DIR / "odai_cards.json")
        self._ctrl = OdaiController(cards=cards)
        self._title_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 14), colors.INK_DARK)
        self._body_r = TextRenderer(ctx.assets.font("PressStart2P-Regular.ttf", 18), colors.INK_DARK)
        self._buttons = [
            Button(pygame.Rect(10, 10, 80, 26), "BACK", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
            Button(pygame.Rect(40, 250, 160, 50), "NEXT", self._next, bg_color=colors.BG_SECONDARY),
            Button(pygame.Rect(280, 250, 160, 50), "QUIT", self._sm.pop, bg_color=colors.ACCENT_BERRY, fg_color=colors.INK_LIGHT),
        ]
        self._next()

    def on_exit(self) -> None:
        pass

    def _next(self) -> None:
        self._current = self._ctrl.next_card()
        if self._ctx.online:
            self._ctx.tts.speak(self._current.text + " は飲む！")

    def handle_event(self, event: InputEvent) -> None:
        for b in self._buttons:
            if b.handle(event):
                return

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(colors.BG_PRIMARY)
        self._title_r.draw(surface, "ODAI", (config.SCREEN_SIZE[0] // 2, 50), anchor="center")
        if self._current:
            self._wrap_draw(surface, self._current.text + " は飲む！", y=130)
        for b in self._buttons:
            b.draw(surface, self._title_r)

    def _wrap_draw(self, surface: pygame.Surface, text: str, y: int) -> None:
        # 簡易折り返し（13文字程度）
        line_len = 13
        lines = [text[i:i + line_len] for i in range(0, len(text), line_len)]
        for i, line in enumerate(lines):
            self._body_r.draw(surface, line, (config.SCREEN_SIZE[0] // 2, y + i * 30), anchor="center")
```

- [ ] **Step 4: テスト実行**

```bash
pytest tests/games/test_odai.py -v
```

期待値：4 PASS。

- [ ] **Step 5: コミット**

```bash
git add nomiboy/data/odai_cards.json nomiboy/src/nomiboy/games/odai.py nomiboy/tests/games/test_odai.py
git commit -m "nomiboy: OdaiScene + OdaiController（30枚同梱、JSON 欠損時フォールバック）"
```

---

# Phase 8: ツールと配布

## Task 24: PCデバッグスクリプト

**Files:**
- Create: `nomiboy/scripts/run_pc.sh`
- Create: `nomiboy/scripts/run_scene.py`

- [ ] **Step 1: `run_pc.sh` を作成**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source venv/bin/activate
PYTHONPATH=src exec python -m nomiboy --windowed
```

- [ ] **Step 2: `run_scene.py` を作成**

```python
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

from nomiboy.app import App


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
    # メインループに乗せ替え
    app.run = app.run.__get__(app, App)  # noop ガード
    # 既存 run() は push_initial_scene を呼ぶので、初期 push を空打ちさせるため上書き
    def run_no_initial(self):
        clock = __import__("pygame").time.Clock()
        import pygame as pg
        running = True
        while running:
            dt = clock.tick(30) / 1000.0
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    running = False
                    break
                if e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE:
                    running = False
                    break
                ev = self.ctx.input_adapter.translate(e)
                if ev is not None:
                    self.sm.handle_event(ev)
            self.sm.update(dt)
            self._screen.fill((255, 203, 5))
            self.sm.draw(self._screen)
            pg.display.flip()
        pg.quit()
    app.run = run_no_initial.__get__(app, App)
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 実行権限を付与**

```bash
chmod +x nomiboy/scripts/run_pc.sh
```

- [ ] **Step 4: コミット**

```bash
git add nomiboy/scripts/run_pc.sh nomiboy/scripts/run_scene.py
git commit -m "nomiboy: PC デバッグ用スクリプト（run_pc.sh, run_scene.py）"
```

---

## Task 25: Pi インストールスクリプト + systemd ユニット

**Files:**
- Create: `nomiboy/scripts/install_pi.sh`
- Create: `nomiboy/scripts/nomiboy.service`

- [ ] **Step 1: systemd ユニットを作成**

`nomiboy/scripts/nomiboy.service`:
```ini
[Unit]
Description=nomiboy drinking-games console
After=multi-user.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/nomiboy
EnvironmentFile=-/home/pi/nomiboy/.env
ExecStart=/home/pi/nomiboy/venv/bin/python -m nomiboy
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: インストールスクリプトを作成**

`nomiboy/scripts/install_pi.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$(pwd)

# 仮想環境
if [ ! -d venv ]; then
  python3.11 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# systemd
sudo cp scripts/nomiboy.service /etc/systemd/system/nomiboy.service
sudo systemctl daemon-reload
sudo systemctl enable nomiboy
echo "Installed. Reboot or run: sudo systemctl start nomiboy"
```

- [ ] **Step 3: 実行権限**

```bash
chmod +x nomiboy/scripts/install_pi.sh
```

- [ ] **Step 4: コミット**

```bash
git add nomiboy/scripts/install_pi.sh nomiboy/scripts/nomiboy.service
git commit -m "nomiboy: Pi 用 systemd ユニットとインストールスクリプト"
```

---

## Task 26: README + .env.example

**Files:**
- Create: `nomiboy/README.md`
- Create: `nomiboy/.env.example`

- [ ] **Step 1: `.env.example`**

```
GEMINI_API_KEY=
NOMIBOY_FULLSCREEN=
NOMIBOY_FORCE_PI=
```

- [ ] **Step 2: `README.md`**

````markdown
# nomiboy

飲み会用ゲーム機。Raspberry Pi Zero 2 + 3.5"SPIタッチディスプレイ + I2Sスピーカーで動く。
PC（macOS/Linux/Windows）でも同じコードでデバッグできる。

## ゲーム
- 爆弾タイマー
- ルーレット
- ○○な人は飲む（Gemini TTS で読み上げ）

## セットアップ
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # GEMINI_API_KEY を設定
```

## 起動

PC（ウィンドウモード）:
```bash
./scripts/run_pc.sh
```

単一シーン（デバッグ用）:
```bash
PYTHONPATH=src python scripts/run_scene.py odai --players たろう,はなこ
```

Raspberry Pi:
```bash
./scripts/install_pi.sh
sudo systemctl start nomiboy
```

## テスト
```bash
PYTHONPATH=src pytest -v
```

## 設計
- 仕様: `docs/superpowers/specs/2026-04-26-nomiboy-design.md`
- 実装計画: `docs/superpowers/plans/2026-04-26-nomiboy-implementation.md`
- ビジュアルガイド: `DESIGN.md`（GBC 風）
````

- [ ] **Step 3: コミット**

```bash
git add nomiboy/README.md nomiboy/.env.example
git commit -m "nomiboy: README と .env.example"
```

---

## Task 27: 新 DESIGN.md（GBC 風）

**Files:**
- Create: `nomiboy/DESIGN.md`

- [ ] **Step 1: GBC 風のデザインドキュメントを作成**（最小骨子。詳細は実装中に詰める）

````markdown
# nomiboy ビジュアルデザイン（GBC カラフル風）

> ステータス: WIP / Task 27 で骨子を作成、実装フェーズで詳細を確定する

## コンセプト
ゲームボーイカラー（GBC）的なポップでカラフルなレトロ感。横持ち 480×320 のレイアウト前提。
飲み会で「楽しさが目に入る」ことを優先し、原色多め・ハイコントラストで構成する。

## カラーパレット（仮）

| 役割 | 値 | 説明 |
|---|---|---|
| BG_PRIMARY | `#FFCB05` | 黄。タイトル・登録・選択画面の基本背景 |
| BG_SECONDARY | `#FF7700` | オレンジ。アクションボタン |
| INK_DARK | `#2B0A3D` | 紫黒。本文・見出し |
| INK_LIGHT | `#FFFFFF` | 白。暗い背景上のテキスト |
| ACCENT_BERRY | `#B03060` | ベリー。BACK 等のシステムボタン |
| ACCENT_LIME | `#9BBC0F` | DMG ライム。+ADD 等の追加系 |
| DANGER_RED | `#DC1E1E` | OFFLINE バッジ・タイマー |

プレイヤー4色: 赤 / 青 / 緑 / 黄。

## タイポグラフィ
- ピクセルフォント（候補: PressStart2P / k8x12 / Misaki Gothic）
- 見出し: 28〜36px / 本文: 14〜18px / キャプション: 10〜12px
- 日本語対応のため、英数字専用フォントとは別に Misaki Gothic 等の和文フォントを併用

## ボタン
- 矩形（角丸なし）+ 1px の濃い枠線
- 押下フィードバックは色相シフト（実装フェーズで決定）

## 画面構成原則
- 480×320 横長
- 上端8px をシステム領域（BACK / OFFLINE バッジ）
- 下端60px をアクションボタン領域

## アニメーション
- TAP TO START の点滅: 0.5s 間隔
- ルーレットのカーソル: 100ms ごとに進行
- 爆弾の数字更新: 60Hz（更新差分）

## 後で詰める
- 各ゲームのアイコン・スプライト
- BGM のトーン（チップチューン or レトロ電子音）
- フォント選定の最終決定
- 押下時のビジュアルフィードバック
````

- [ ] **Step 2: コミット**

```bash
git add nomiboy/DESIGN.md
git commit -m "nomiboy: GBC 風デザインの骨子（仮配色・タイポ）"
```

---

# Phase 9: 統合確認

## Task 28: 全テスト実行と PC 起動確認

- [ ] **Step 1: 全テスト実行**

```bash
cd nomiboy && source venv/bin/activate
PYTHONPATH=src pytest -v
```

期待値：すべて PASS（30件以上）。

- [ ] **Step 2: PC で起動して全画面遷移を手動確認**

```bash
./scripts/run_pc.sh
```

確認項目：
- Title 表示 → tap で PlayerRegister へ
- + ADD でキーボード起動 → 「たろう」入力 → OK で登録される
- 4人まで追加 → + ADD ボタンが消える
- 2人未満では START ボタンが灰色（押せない）
- START → GameSelect へ
- BOMB → タイマー進行 → PASS で持ち回り → 0秒で Result
- ROULETTE → STOP で抽選 → Result
- ODAI → カード表示 → NEXT で別カード → QUIT で GameSelect
- TITLE ボタンで Title へ戻る（プレイヤーリセット）
- ESCキーで終了

- [ ] **Step 3: 単一シーンモードを動作確認**

```bash
PYTHONPATH=src python scripts/run_scene.py odai --players a,b
```

期待値：いきなり OdaiScene が起動して動く。

- [ ] **Step 4: 動作 OK ならコミット不要、課題があれば修正してコミット**

問題があった場合は対応する Task に戻って修正 → コミット。

---

## Task 29: Gemini TTS 実 API 連携（後付け、任意）

**Files:**
- Modify: `nomiboy/src/nomiboy/core/tts_service.py`

> **注：** 本タスクは GEMINI_API_KEY を持っていて実機で確認できる場合のみ。テスト不可（実APIアクセス）。

- [ ] **Step 1: `_synthesize` を実装**（google-genai を使用）

`tts_service.py` の `_synthesize` を以下に置き換え：

```python
def _synthesize(self, text: str, voice: str) -> bytes | None:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=self._api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
                )
            ),
        ),
    )
    audio = response.candidates[0].content.parts[0].inline_data.data
    return audio
```

> 注: Gemini TTS API のスキーマは変わる可能性があるため、実装時に `context7` で最新ドキュメントを参照すること。

- [ ] **Step 2: 実機で発話を確認**

```bash
GEMINI_API_KEY=xxx PYTHONPATH=src python scripts/run_scene.py odai --players a,b
```

- [ ] **Step 3: コミット（成功時のみ）**

```bash
git add nomiboy/src/nomiboy/core/tts_service.py
git commit -m "nomiboy: Gemini TTS 実 API 連携"
```

---

# 完成基準

以下が満たされたら MVP 完成：

1. PC（macOS）で `./scripts/run_pc.sh` から起動・全画面遷移できる
2. すべてのユニットテストが PASS
3. Pi で `install_pi.sh` 後、systemd 自動起動して動作する（実機確認は別途）
4. プレイヤー登録 → ゲーム選択 → 爆弾/ルーレット/お題が一通り遊べる
5. オフライン時もゲームが動く（TTS のみ無効）

> **完成後にやること（spec 12 章「後で詰める」）：** 各ゲームの演出・アセット調達・GBC パレット最終確定・Geminiの音声バリエーション・物理ボタン拡張は MVP 後の改善イテレーション。
