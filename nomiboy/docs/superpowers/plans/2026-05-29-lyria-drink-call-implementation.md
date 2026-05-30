# Lyria 3 ドリンクコール 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gemini Lyria 3 を使い、負けたプレイヤー名入りのコール曲をゲーム開始時に並列プリフェッチし、Result シーンで再生する共通サービスを実装する。

**Architecture:** `LyriaService`（API ラッパー）と `CallPlayer`（プリフェッチ + 再生フック）を core に追加。`AppContext` に `CallPlayer` を注入し、`GameSelectScene` でゲーム起動時に `prefetch`、`ResultScene` で `play` する。全失敗パスは無音スキップ。

**Tech Stack:** Python 3.11 / pygame / google-genai (>= 0.3) / concurrent.futures.ThreadPoolExecutor / pytest

**Spec:** `docs/superpowers/specs/2026-05-29-lyria-drink-call-design.md`

---

## ファイル構成

| 種別 | パス | 役割 |
|---|---|---|
| 新規 | `src/nomiboy/core/lyria_service.py` | Lyria 3 API ラッパー + `CallTemplate` |
| 新規 | `src/nomiboy/core/call_player.py` | プリフェッチ + プレイヤーごとの Sound 再生 |
| 新規 | `data/call_prompts.json` | プロンプトテンプレート集 |
| 新規 | `tests/test_lyria_service.py` | LyriaService 単体テスト |
| 新規 | `tests/test_call_player.py` | CallPlayer 単体テスト |
| 修正 | `src/nomiboy/config.py` | Lyria 関連定数追加 |
| 修正 | `src/nomiboy/app.py` | AppContext に CallPlayer を追加 |
| 修正 | `src/nomiboy/scenes/game_select.py` | `_launch` 内で prefetch |
| 修正 | `src/nomiboy/scenes/result.py` | tts.speak を call_player.play に置換 |
| 修正 | `tests/test_config.py` | 新規定数の検証 |

---

## Task 1: config に Lyria 定数を追加

**Files:**
- Modify: `src/nomiboy/config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_config.py` の末尾に追加:

```python
def test_lyria_constants_exist():
    from nomiboy import config

    assert config.LYRIA_MODEL == "lyria-3-pro-preview"
    assert config.LYRIA_TIMEOUT_SEC == 60
    assert config.LYRIA_PREFETCH_WORKERS == 4
    assert config.LYRIA_PLAY_WAIT_SEC == 1.5
    assert config.CALL_PROMPTS_PATH.name == "call_prompts.json"


def test_disable_lyria_env(monkeypatch):
    monkeypatch.setenv("NOMIBOY_DISABLE_LYRIA", "1")
    import importlib

    from nomiboy import config as cfg

    importlib.reload(cfg)
    assert cfg.DISABLE_LYRIA is True
    monkeypatch.delenv("NOMIBOY_DISABLE_LYRIA")
    importlib.reload(cfg)
    assert cfg.DISABLE_LYRIA is False
```

- [ ] **Step 2: テストを実行して失敗確認**

Run: `PYTHONPATH=src pytest tests/test_config.py -v`
Expected: `test_lyria_constants_exist` が `AttributeError: module 'nomiboy.config' has no attribute 'LYRIA_MODEL'` で失敗

- [ ] **Step 3: `config.py` に定数を追加**

`src/nomiboy/config.py` の末尾 (`LOG_DIR = ...` の下) に追記:

```python
LYRIA_MODEL = "lyria-3-pro-preview"
LYRIA_TIMEOUT_SEC = 60
LYRIA_PREFETCH_WORKERS = 4
LYRIA_PLAY_WAIT_SEC = 1.5
CALL_PROMPTS_PATH = DATA_DIR / "call_prompts.json"
DISABLE_LYRIA = os.environ.get("NOMIBOY_DISABLE_LYRIA") == "1"
```

- [ ] **Step 4: テスト通過確認**

Run: `PYTHONPATH=src pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: コミット**

```bash
git add src/nomiboy/config.py tests/test_config.py
git commit -m "nomiboy: config に Lyria 関連定数を追加"
```

---

## Task 2: コールプロンプトの JSON を追加

**Files:**
- Create: `data/call_prompts.json`

- [ ] **Step 1: JSON ファイルを作成**

`data/call_prompts.json`:

```json
[
  {
    "style": "upbeat J-pop party chant with crowd cheering, 120bpm, energetic vocals",
    "lyrics_template": "Lyrics:\n[Chorus]\n{name} が飲んで！ 飲んで！ 飲んで！\n{name} が飲んで！ 飲んで！ 飲んで！",
    "duration_sec": 12
  },
  {
    "style": "retro chiptune game over fanfare with vocal shout, 8bit",
    "lyrics_template": "Lyrics:\n[Chorus]\n{name}！ のんで のんで のんで！\n{name}！ のんで のんで のんで！",
    "duration_sec": 10
  },
  {
    "style": "EDM festival drop with cheering crowd, 128bpm",
    "lyrics_template": "Lyrics:\n[Drop]\nDrink {name}! drink drink drink!\nDrink {name}! drink drink drink!",
    "duration_sec": 12
  },
  {
    "style": "japanese taiko drum chant with festival vibe",
    "lyrics_template": "Lyrics:\n[Chorus]\nそーれ {name}！ 飲んで 飲んで 飲んで！",
    "duration_sec": 10
  }
]
```

- [ ] **Step 2: JSON 構造の sanity check**

Run: `python -c "import json; print(len(json.load(open('data/call_prompts.json'))))"`
Expected: `4`

- [ ] **Step 3: コミット**

```bash
git add data/call_prompts.json
git commit -m "nomiboy: ドリンクコール用プロンプトテンプレートを追加"
```

---

## Task 3: CallTemplate dataclass と LyriaService スケルトン (API キー未設定時)

**Files:**
- Create: `src/nomiboy/core/lyria_service.py`
- Create: `tests/test_lyria_service.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_lyria_service.py`:

```python
"""LyriaService 単体テスト。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from nomiboy.core.lyria_service import CallTemplate, LyriaService


def _tmpl() -> CallTemplate:
    return CallTemplate(
        style="upbeat chant",
        lyrics_template="Lyrics:\n[Chorus]\n{name} が飲んで！",
        duration_sec=10,
    )


def test_synthesize_returns_none_when_api_key_missing():
    svc = LyriaService(api_key=None)
    assert svc.synthesize_call("たろう", _tmpl()) is None


def test_synthesize_returns_none_when_disabled():
    svc = LyriaService(api_key="dummy", disabled=True)
    assert svc.synthesize_call("たろう", _tmpl()) is None


def test_calltemplate_substitutes_name():
    t = _tmpl()
    assert "{name}" in t.lyrics_template
    assert "たろう" in t.lyrics_template.replace("{name}", "たろう")
```

- [ ] **Step 2: テスト実行して失敗確認**

Run: `PYTHONPATH=src pytest tests/test_lyria_service.py -v`
Expected: `ModuleNotFoundError: No module named 'nomiboy.core.lyria_service'`

- [ ] **Step 3: スケルトン実装**

`src/nomiboy/core/lyria_service.py`:

```python
"""Gemini Lyria 3 サービス。人名入りコール曲を生成する。

API キー未設定 / disabled / ネット失敗時はすべて None を返す。
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CallTemplate:
    style: str
    lyrics_template: str  # "{name}" を含む
    duration_sec: int


class LyriaService:
    def __init__(
        self,
        api_key: str | None,
        model: str = "lyria-3-pro-preview",
        timeout_sec: float = 60.0,
        disabled: bool = False,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_sec
        self._disabled = disabled

    def synthesize_call(self, player_name: str, template: CallTemplate) -> bytes | None:
        if self._disabled or not self._api_key:
            return None
        try:
            return self._generate(player_name, template)
        except Exception as e:
            log.warning("Lyria generation failed for %s: %s", player_name, e)
            return None

    def _generate(self, player_name: str, template: CallTemplate) -> bytes | None:
        """Task 4 で実装。"""
        raise NotImplementedError
```

- [ ] **Step 4: テスト通過確認**

Run: `PYTHONPATH=src pytest tests/test_lyria_service.py -v`
Expected: 3 つ PASS

- [ ] **Step 5: コミット**

```bash
git add src/nomiboy/core/lyria_service.py tests/test_lyria_service.py
git commit -m "nomiboy: LyriaService スケルトン + CallTemplate を追加"
```

---

## Task 4: LyriaService の API 呼び出し実装

**Files:**
- Modify: `src/nomiboy/core/lyria_service.py`
- Modify: `tests/test_lyria_service.py`

- [ ] **Step 1: モック化した正常系テストを追加**

`tests/test_lyria_service.py` の末尾に追加:

```python
def test_generate_calls_genai_and_returns_bytes():
    fake_audio = b"FAKE_WAV_BYTES"
    fake_part = MagicMock()
    fake_part.inline_data.data = fake_audio
    fake_response = MagicMock()
    fake_response.candidates = [MagicMock()]
    fake_response.candidates[0].content.parts = [fake_part]

    with patch("nomiboy.core.lyria_service.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = fake_response
        mock_genai.Client.return_value = mock_client

        svc = LyriaService(api_key="dummy-key")
        result = svc.synthesize_call("たろう", _tmpl())

    assert result == fake_audio
    mock_genai.Client.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "lyria-3-pro-preview"
    # プロンプトに名前が含まれている
    contents_arg = call_kwargs["contents"]
    text_payload = str(contents_arg)
    assert "たろう" in text_payload
    assert "upbeat chant" in text_payload


def test_generate_returns_none_on_exception():
    with patch("nomiboy.core.lyria_service.genai") as mock_genai:
        mock_genai.Client.side_effect = RuntimeError("boom")
        svc = LyriaService(api_key="dummy-key")
        assert svc.synthesize_call("たろう", _tmpl()) is None


def test_generate_returns_none_when_no_audio_part():
    with patch("nomiboy.core.lyria_service.genai") as mock_genai:
        mock_client = MagicMock()
        empty_response = MagicMock()
        empty_response.candidates = []
        mock_client.models.generate_content.return_value = empty_response
        mock_genai.Client.return_value = mock_client

        svc = LyriaService(api_key="dummy-key")
        assert svc.synthesize_call("たろう", _tmpl()) is None
```

- [ ] **Step 2: テスト失敗確認**

Run: `PYTHONPATH=src pytest tests/test_lyria_service.py -v`
Expected: `test_generate_*` が `NotImplementedError` で失敗

- [ ] **Step 3: `_generate` を実装**

`src/nomiboy/core/lyria_service.py` の先頭インポートに追加:

```python
from google import genai
from google.genai import types
```

`_generate` メソッドを以下に置換:

```python
    def _generate(self, player_name: str, template: CallTemplate) -> bytes | None:
        prompt = self._build_prompt(player_name, template)
        client = genai.Client(api_key=self._api_key)
        response = client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
            ),
        )
        if not response.candidates:
            return None
        parts = response.candidates[0].content.parts
        for part in parts:
            data = getattr(getattr(part, "inline_data", None), "data", None)
            if data:
                return data if isinstance(data, bytes) else bytes(data)
        return None

    @staticmethod
    def _build_prompt(player_name: str, template: CallTemplate) -> str:
        lyrics = template.lyrics_template.replace("{name}", player_name)
        return (
            f"{template.style}\n"
            f"Duration: about {template.duration_sec} seconds.\n\n"
            f"{lyrics}"
        )
```

- [ ] **Step 4: テスト通過確認**

Run: `PYTHONPATH=src pytest tests/test_lyria_service.py -v`
Expected: 全 PASS

- [ ] **Step 5: コミット**

```bash
git add src/nomiboy/core/lyria_service.py tests/test_lyria_service.py
git commit -m "nomiboy: LyriaService の Gemini 呼び出しを実装"
```

---

## Task 5: CallPlayer スケルトンと load_call_templates

**Files:**
- Create: `src/nomiboy/core/call_player.py`
- Create: `tests/test_call_player.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_call_player.py`:

```python
"""CallPlayer 単体テスト。"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from nomiboy.core.call_player import CallPlayer, load_call_templates
from nomiboy.core.lyria_service import CallTemplate
from nomiboy.stores.player_store import Player


def _player(pid: int = 1, name: str = "たろう") -> Player:
    return Player(id=pid, name=name, color=(255, 0, 0))


def _templates() -> list[CallTemplate]:
    return [
        CallTemplate(style="s1", lyrics_template="Lyrics:\n{name}", duration_sec=10),
    ]


def test_load_call_templates_from_json(tmp_path: Path):
    payload = [
        {"style": "s", "lyrics_template": "Lyrics:\n{name}", "duration_sec": 10},
    ]
    p = tmp_path / "call_prompts.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    templates = load_call_templates(p)
    assert len(templates) == 1
    assert templates[0].style == "s"


def test_load_call_templates_returns_default_when_missing(tmp_path: Path):
    p = tmp_path / "missing.json"
    templates = load_call_templates(p)
    assert len(templates) >= 1
    assert "{name}" in templates[0].lyrics_template


def test_play_returns_false_when_no_future():
    lyria = MagicMock()
    audio = MagicMock()
    cp = CallPlayer(lyria=lyria, audio=audio, templates=_templates())
    assert cp.play(_player()) is False
```

- [ ] **Step 2: テスト失敗確認**

Run: `PYTHONPATH=src pytest tests/test_call_player.py -v`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: スケルトン実装**

`src/nomiboy/core/call_player.py`:

```python
"""ドリンクコール再生サービス。ゲーム開始時に全員分をプリフェッチし、負け確定時に再生する。"""
from __future__ import annotations

import io
import json
import logging
import random
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

import pygame

from nomiboy.core.audio_service import AudioService
from nomiboy.core.lyria_service import CallTemplate, LyriaService
from nomiboy.stores.player_store import Player

log = logging.getLogger(__name__)

_DEFAULT_TEMPLATE = CallTemplate(
    style="upbeat J-pop party chant with crowd cheering",
    lyrics_template="Lyrics:\n[Chorus]\n{name} が飲んで！ 飲んで！ 飲んで！",
    duration_sec=10,
)


def load_call_templates(path: Path) -> list[CallTemplate]:
    """JSON からテンプレ集をロード。失敗時はデフォルト 1 件を返す。"""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [
            CallTemplate(
                style=item["style"],
                lyrics_template=item["lyrics_template"],
                duration_sec=int(item["duration_sec"]),
            )
            for item in raw
        ]
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
        log.warning("call_prompts.json load failed (%s); using default", e)
        return [_DEFAULT_TEMPLATE]


class CallPlayer:
    def __init__(
        self,
        lyria: LyriaService,
        audio: AudioService,
        templates: list[CallTemplate],
        max_workers: int = 4,
        play_wait_sec: float = 1.5,
    ) -> None:
        self._lyria = lyria
        self._audio = audio
        self._templates = templates or [_DEFAULT_TEMPLATE]
        self._max_workers = max_workers
        self._play_wait = play_wait_sec
        self._executor: ThreadPoolExecutor | None = None
        self._futures: dict[int, Future[pygame.mixer.Sound | None]] = {}

    def prefetch(self, players: list[Player]) -> None:
        """全員分の生成をバックグラウンドで開始。即 return。"""
        self.clear()
        if not players:
            return
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        for p in players:
            tmpl = random.choice(self._templates)
            self._futures[p.id] = self._executor.submit(self._generate_one, p.name, tmpl)

    def play(self, player: Player) -> bool:
        """プレイヤーに対応する Sound を再生。完了済 or 短時間待機。"""
        future = self._futures.get(player.id)
        if future is None:
            return False
        try:
            sound = future.result(timeout=self._play_wait)
        except Exception as e:
            log.warning("call play wait failed for %s: %s", player.name, e)
            return False
        if sound is None:
            return False
        sound.play()
        return True

    def clear(self) -> None:
        """Future をキャンセルし、状態をリセット。"""
        for f in self._futures.values():
            f.cancel()
        self._futures.clear()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def _generate_one(self, name: str, template: CallTemplate) -> "pygame.mixer.Sound | None":
        wav_bytes = self._lyria.synthesize_call(name, template)
        if not wav_bytes:
            return None
        try:
            return pygame.mixer.Sound(io.BytesIO(wav_bytes))
        except Exception as e:
            log.warning("Sound load failed for %s: %s", name, e)
            return None
```

- [ ] **Step 4: テスト通過確認**

Run: `PYTHONPATH=src pytest tests/test_call_player.py -v`
Expected: 3 つ PASS

- [ ] **Step 5: コミット**

```bash
git add src/nomiboy/core/call_player.py tests/test_call_player.py
git commit -m "nomiboy: CallPlayer スケルトン + テンプレート読み込みを追加"
```

---

## Task 6: CallPlayer の prefetch と play の振る舞いをテスト

**Files:**
- Modify: `tests/test_call_player.py`

- [ ] **Step 1: prefetch と play のテストを追加**

`tests/test_call_player.py` の末尾に追加:

```python
def test_prefetch_calls_lyria_for_each_player(monkeypatch):
    lyria = MagicMock()
    lyria.synthesize_call.return_value = b"FAKEWAV"
    audio = MagicMock()

    fake_sound = MagicMock()
    monkeypatch.setattr("nomiboy.core.call_player.pygame.mixer.Sound", lambda _bio: fake_sound)

    cp = CallPlayer(lyria=lyria, audio=audio, templates=_templates(), max_workers=2, play_wait_sec=2.0)
    players = [_player(1, "たろう"), _player(2, "はなこ")]
    cp.prefetch(players)

    assert cp.play(players[0]) is True
    assert cp.play(players[1]) is True
    fake_sound.play.assert_called()
    assert lyria.synthesize_call.call_count == 2
    cp.clear()


def test_prefetch_with_failed_generation_returns_false(monkeypatch):
    lyria = MagicMock()
    lyria.synthesize_call.return_value = None  # 失敗
    audio = MagicMock()

    cp = CallPlayer(lyria=lyria, audio=audio, templates=_templates(), max_workers=1, play_wait_sec=1.0)
    p = _player(1, "たろう")
    cp.prefetch([p])

    assert cp.play(p) is False
    cp.clear()


def test_prefetch_empty_list_is_noop():
    lyria = MagicMock()
    cp = CallPlayer(lyria=lyria, audio=MagicMock(), templates=_templates())
    cp.prefetch([])
    assert cp.play(_player()) is False


def test_clear_resets_state(monkeypatch):
    lyria = MagicMock()
    lyria.synthesize_call.return_value = b"FAKE"
    monkeypatch.setattr("nomiboy.core.call_player.pygame.mixer.Sound", lambda _bio: MagicMock())

    cp = CallPlayer(lyria=lyria, audio=MagicMock(), templates=_templates())
    cp.prefetch([_player(1)])
    cp.clear()
    assert cp.play(_player(1)) is False
```

- [ ] **Step 2: テスト実行**

Run: `PYTHONPATH=src pytest tests/test_call_player.py -v`
Expected: 全 PASS（既存実装で通る想定）

- [ ] **Step 3: コミット**

```bash
git add tests/test_call_player.py
git commit -m "nomiboy: CallPlayer の prefetch/play/clear 振る舞いテストを追加"
```

---

## Task 7: AppContext に CallPlayer を統合

**Files:**
- Modify: `src/nomiboy/app.py`

- [ ] **Step 1: app.py を編集**

`src/nomiboy/app.py` の import セクションに追加:

```python
from nomiboy.core.call_player import CallPlayer, load_call_templates
from nomiboy.core.lyria_service import LyriaService
```

`AppContext` dataclass に `call_player` フィールドを追加:

```python
@dataclass
class AppContext:
    config: ModuleType
    input_adapter: InputAdapter
    audio: AudioService
    tts: TTSService
    players: PlayerStore
    assets: AssetLoader
    online: bool
    call_player: CallPlayer
```

`App.__init__` 内で AppContext を構築する部分を以下に置換:

```python
        api_key = os.environ.get("GEMINI_API_KEY")
        lyria = LyriaService(
            api_key=api_key,
            model=config.LYRIA_MODEL,
            timeout_sec=config.LYRIA_TIMEOUT_SEC,
            disabled=config.DISABLE_LYRIA,
        )
        call_templates = load_call_templates(config.CALL_PROMPTS_PATH)
        audio = AudioService()
        self.ctx = AppContext(
            config=config,
            input_adapter=InputAdapter(config.SCREEN_SIZE),
            audio=audio,
            tts=TTSService(api_key=api_key),
            players=PlayerStore(),
            assets=AssetLoader(),
            online=_check_online(),
            call_player=CallPlayer(
                lyria=lyria,
                audio=audio,
                templates=call_templates,
                max_workers=config.LYRIA_PREFETCH_WORKERS,
                play_wait_sec=config.LYRIA_PLAY_WAIT_SEC,
            ),
        )
```

- [ ] **Step 2: 既存テストが落ちないか確認**

Run: `PYTHONPATH=src pytest -v`
Expected: 既存テスト全 PASS、新規テストも全 PASS

- [ ] **Step 3: PC ウィンドウモードで起動して落ちないか確認**

Run: `./scripts/run_pc.sh`
Expected: タイトル画面が表示される（ESC で終了）

- [ ] **Step 4: コミット**

```bash
git add src/nomiboy/app.py
git commit -m "nomiboy: AppContext に CallPlayer / LyriaService を統合"
```

---

## Task 8: GameSelectScene でゲーム起動時に prefetch

**Files:**
- Modify: `src/nomiboy/scenes/game_select.py`

- [ ] **Step 1: `_launch` メソッドの先頭で prefetch を呼ぶよう変更**

`src/nomiboy/scenes/game_select.py` の `_launch` を以下に置換:

```python
    def _launch(self, key: str) -> None:
        # 負け確定時のドリンクコールを並列プリフェッチ（即 return、ノンブロッキング）
        if self._ctx is not None:
            self._ctx.call_player.prefetch(self._ctx.players.players)

        if key == "bomb":
            from nomiboy.games.bomb import BombScene

            self._sm.push(BombScene(self._sm))
        elif key == "roulette":
            from nomiboy.games.roulette import RouletteScene

            self._sm.push(RouletteScene(self._sm))
        elif key == "odai":
            from nomiboy.games.odai import OdaiScene

            self._sm.push(OdaiScene(self._sm))
        elif key == "russian_tap":
            from nomiboy.games.russian_tap import RussianTapScene

            self._sm.push(RussianTapScene(self._sm))
```

- [ ] **Step 2: 既存テストが落ちないか確認**

Run: `PYTHONPATH=src pytest tests/test_game_select_paging.py -v`
Expected: 既存テスト全 PASS

- [ ] **Step 3: コミット**

```bash
git add src/nomiboy/scenes/game_select.py
git commit -m "nomiboy: ゲーム起動時にドリンクコールを並列プリフェッチ"
```

---

## Task 9: ResultScene で call_player.play を呼ぶ

**Files:**
- Modify: `src/nomiboy/scenes/result.py`

- [ ] **Step 1: `on_enter` を編集**

`src/nomiboy/scenes/result.py` の `on_enter` を以下に置換:

```python
    def on_enter(self, ctx: AppContext) -> None:
        self._title_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 28), colors.INK_DARK)
        self._sub_r = TextRenderer(ctx.assets.font("DotGothic16-Regular.ttf", 12), colors.INK_DARK)
        played = ctx.call_player.play(self._loser)
        if not played and ctx.online:
            # Lyria が失敗した時のみ既存 TTS でコールを読み上げ
            ctx.tts.speak(f"{self._loser.name} は飲む！")
```

- [ ] **Step 2: 全テスト実行**

Run: `PYTHONPATH=src pytest -v`
Expected: 全 PASS

- [ ] **Step 3: コミット**

```bash
git add src/nomiboy/scenes/result.py
git commit -m "nomiboy: Result で Lyria ドリンクコールを再生（失敗時 TTS フォールバック）"
```

---

## Task 10: PC ウィンドウモードで E2E 動作確認

**Files:**
- None (動作確認のみ)

- [ ] **Step 1: `.env` に `GEMINI_API_KEY` が入っているか確認**

Run: `grep -q '^GEMINI_API_KEY=' .env && echo "OK" || echo "MISSING"`
Expected: `OK`（無ければ `.env.example` を参考に設定）

- [ ] **Step 2: PC ウィンドウモードで起動**

Run: `./scripts/run_pc.sh`

- [ ] **Step 3: 以下の手動シナリオを確認**

1. タイトル → タップ
2. プレイヤー登録で 2 名追加（例: たろう / はなこ）
3. SELECT GAME で `bomb` を選択
4. **裏で Lyria 生成が走り始める想定**（ログに `Lyria` 関連なし、エラーも出ないこと）
5. 爆弾ゲームを通常プレイし負けを発生させる
6. Result シーンで 1.5 秒以内に名前入りコール曲が再生される

期待:
- 音が鳴る（API キー設定済の場合）
- API キー未設定 or オフラインなら無音でそのまま画面表示

- [ ] **Step 4: `NOMIBOY_DISABLE_LYRIA=1` で無音確認**

Run: `PYTHONPATH=src NOMIBOY_DISABLE_LYRIA=1 NOMIBOY_FULLSCREEN=0 python -m nomiboy --windowed`

Result シーンで音が鳴らずに画面遷移すること。

- [ ] **Step 5: ログ確認**

Run: `tail -50 ~/.nomiboy/log.txt`
Expected: Tracebacks なし。Lyria 失敗時は WARN のみ

- [ ] **Step 6: 確認結果を記録するコミット（手動 QA メモ）**

このタスクではコード変更がないため、E2E 結果に応じて以下のどちらか:

- 問題なし → 完了
- 問題あり → 個別 Task として追加

---

## 自己レビューチェック

- [x] Spec の「ゴール 1〜4」を Task 1〜10 でカバー（受け入れ条件 5 は Task 9 までの `pytest -v` 全 PASS で満たす）
- [x] プレースホルダーなし、全タスクに具体コード
- [x] `CallTemplate` のフィールド名 (`style` / `lyrics_template` / `duration_sec`) は全タスクで統一
- [x] `LyriaService.synthesize_call(player_name, template)` シグネチャは Task 3/4/5/6 で統一
- [x] `CallPlayer.prefetch(players)` / `play(player)` / `clear()` シグネチャは Task 5/6/7/8/9 で統一
- [x] `AppContext.call_player` は Task 7 で追加、Task 8/9 で参照
- [x] `config.LYRIA_*` / `config.CALL_PROMPTS_PATH` / `config.DISABLE_LYRIA` は Task 1 で追加、Task 7 で参照
