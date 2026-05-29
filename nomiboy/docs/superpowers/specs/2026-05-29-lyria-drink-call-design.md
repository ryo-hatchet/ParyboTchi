# Lyria 3 ドリンクコール 設計

> ステータス: 設計確定 / 2026-05-29 ブレスト承認済み
> 関連: `core/tts_service.py`（既存 Gemini TTS、置換せず共存）

## 目的

負けたプレイヤーの名前を含んだ「XXX が飲んで！飲んで！飲んで！」というコール風楽曲を生成・再生し、飲み会の盛り上がりを演出する。

## ゴール / 非ゴール

### ゴール
- Gemini Lyria 3 (`lyria-3-pro-preview`) で人名入りの短尺コール曲を生成
- 全ゲーム（bomb / roulette / russian_tap）から共通サービスとして利用可能にする
- ゲーム開始時に全プレイヤー分をバックグラウンド並列生成し、負け確定時の待ち時間をゼロに近づける
- 生成失敗・オフライン・API キー未設定でも無音スキップしてゲーム継続

### 非ゴール
- ディスクキャッシュ（セッション中のみメモリ保持）
- BGM とのミックス（コール曲自体が音楽のため不要）
- odai ゲームでの利用（フェーズ 2 で別途検討）
- 多言語対応（日本語固定）
- ElevenLabs 等 Lyria 以外のプロバイダ

## 全体像

```
[GameSelect: ゲーム選択]
        │
        ▼
[CallPlayer.prefetch(players)]  ── ThreadPoolExecutor で N 並列
        │   ├─ player1 → LyriaService → bytes → pygame Sound
        │   ├─ player2 → LyriaService → bytes → pygame Sound
        │   └─ ...                                         dict に格納
        ▼
[ゲームプレイ進行]   ← 並列で生成が完了
        │
        ▼
[各ゲームで負け確定]
        │
        ▼
[CallPlayer.play(loser)]
        ├─ 完了済    → mixer 再生
        ├─ 進行中    → 最大 LYRIA_PLAY_WAIT_SEC 秒待機 → 再生 or 無音
        └─ 失敗/None → 無音スキップ
        ▼
[Result シーン表示（既存）]
```

## コンポーネント

### `core/lyria_service.py` 新規

```python
class LyriaService:
    def __init__(
        self,
        api_key: str | None,
        model: str = "lyria-3-pro-preview",
        timeout_sec: float = 60.0,
    ) -> None: ...

    def synthesize_call(
        self,
        player_name: str,
        template: CallTemplate,
    ) -> bytes | None:
        """WAV バイト列を返す。失敗時 None。"""
```

- 内部で `google.genai.Client` の `generateContent` を呼び出す
- レスポンス形式: `responseModalities=["AUDIO"]`, `responseFormat.audio.mimeType="audio/wav"`
- 例外は全て吸収し WARN ログを残して None
- API キー未設定時は即座に None

### `core/call_player.py` 新規

```python
@dataclass(frozen=True)
class CallTemplate:
    style: str
    lyrics_template: str   # "{name}" を placeholder として持つ
    duration_sec: int


class CallPlayer:
    def __init__(self, lyria: LyriaService, audio: AudioService, templates: list[CallTemplate]) -> None: ...

    def prefetch(self, players: list[Player]) -> None:
        """全員分の生成をバックグラウンドで開始。即 return。"""

    def play(self, player: Player) -> bool:
        """その場で再生（完了済 or 短時間待機）。再生できた場合 True。"""

    def clear(self) -> None:
        """セッション終了時に Future と Sound を破棄。"""
```

- `ThreadPoolExecutor(max_workers=LYRIA_PREFETCH_WORKERS)` を `prefetch` 時に生成
- `Future` の結果は `dict[player_id, pygame.mixer.Sound | None]` に格納
- `prefetch` を同一セッションで複数回呼ばれたら、前回の Future はキャンセル + clear
- テンプレートは `random.choice(templates)` で各プレイヤーごとに 1 つ選ぶ

### `data/call_prompts.json` 新規

3〜5 種類のテンプレートを格納。例:

```json
[
  {
    "style": "upbeat J-pop party chant with crowd cheering, 120bpm",
    "lyrics_template": "Lyrics:\n[Chorus]\n{name} が飲んで！飲んで！飲んで！\n{name} が飲んで！飲んで！飲んで！",
    "duration_sec": 12
  },
  {
    "style": "retro chiptune game over fanfare with vocal shout",
    "lyrics_template": "Lyrics:\n[Chorus]\n{name}！ のんで のんで のんで！",
    "duration_sec": 10
  },
  {
    "style": "EDM festival drop with cheer crowd",
    "lyrics_template": "Lyrics:\n[Drop]\nDrink {name}! drink drink drink!",
    "duration_sec": 12
  }
]
```

Lyria に渡す最終プロンプトは `synthesize_call` 内で組み立てる:

```
{template.style}
Duration: about {duration_sec} seconds.

{template.lyrics_template.replace("{name}", player_name)}
```

### `config.py` 追加

```python
LYRIA_MODEL = "lyria-3-pro-preview"
LYRIA_TIMEOUT_SEC = 60
LYRIA_PREFETCH_WORKERS = 4
LYRIA_PLAY_WAIT_SEC = 1.5
CALL_PROMPTS_PATH = DATA_DIR / "call_prompts.json"
DISABLE_LYRIA = os.environ.get("NOMIBOY_DISABLE_LYRIA") == "1"
```

### `app.py` 修正

- `AppContext` に `call_player: CallPlayer` を追加
- 起動時に `LyriaService(api_key=GEMINI_API_KEY)` と `CallPlayer` を初期化

### `scenes/game_select.py` 修正

- ゲーム選択時、選択した game シーンに遷移する直前に `ctx.call_player.prefetch(ctx.players)` を呼ぶ
- 既に同一プレイヤー集合で prefetch 済みなら再実行しない（簡易キーで判定）

### `scenes/result.py` 修正

- `on_enter` の現在の `ctx.tts.speak(...)` を **削除**し、代わりに `ctx.call_player.play(self._loser)` を呼ぶ
- 既存の Gemini TTS 呼び出しは odai 等で使うため `TTSService` 自体は残す

### ゲーム側の修正

- bomb / roulette / russian_tap いずれも負け確定時に `ResultScene(self._sm, loser)` を push する作りなので、`result.py` 側に `call_player.play(loser)` を入れれば全ゲーム共通で動作する
- 個別ゲームファイル (`games/bomb.py` / `games/roulette.py` / `games/russian_tap.py`) は **修正不要**

## エラー処理

| 状況 | 動作 |
|---|---|
| `GEMINI_API_KEY` 未設定 / `NOMIBOY_DISABLE_LYRIA=1` | `prefetch` 即 skip、`play` は False |
| ネットワークなし | 個別 Future が例外、dict に None 格納、`play` は False |
| Lyria API HTTP エラー | WARN ログ + None |
| タイムアウト（60s） | `Future.result(timeout=...)` の `TimeoutError` を捕捉、None |
| 安全フィルタブロック（人名で稀に発生） | レスポンス空 / 例外 → None |
| `play` 時に Future が未完了 | `LYRIA_PLAY_WAIT_SEC` (1.5s) だけ待機、それでも未完なら無音 |
| `call_prompts.json` が読めない | デフォルトテンプレート 1 件をハードコードで提供 |

## 設定 / 環境変数

- `GEMINI_API_KEY`（既存、`.env.example` に記載済み）
- `NOMIBOY_DISABLE_LYRIA=1` を新規追加（デバッグ用に Lyria を強制無効化）

## テスト

`tests/test_lyria_service.py`
- API キー未設定 → `synthesize_call` が None
- `google.genai.Client` を mock し、正常系で bytes を返す
- API 例外発生時に None を返す

`tests/test_call_player.py`
- `prefetch` 後にすぐ `play` を呼ぶと最大 1.5 秒待機して結果を返す
- 完了済みプレイヤーで再生関数（mock）が呼ばれる
- 失敗プレイヤーで `play` が False
- `clear` で Future がキャンセルされる
- LyriaService を mock 化、`pygame.mixer.Sound` も `unittest.mock.MagicMock` で代替

`tests/test_config.py`（既存に追加）
- 新規定数の読み込み確認

## 受け入れ条件

1. `GEMINI_API_KEY` 設定済 + ネット環境で、bomb ゲーム実行 → 負け確定時に該当プレイヤー名入りコール曲が再生される
2. ゲーム選択から負け確定まで通常プレイで 20 秒以上経過する想定下で、再生時の追加待ちが 1.5 秒以内
3. API キー未設定 / オフライン時にゲームが落ちず無音で進行
4. russian_tap / roulette でも同様に再生される
5. `pytest -v` 全パス

## スコープ外（将来）

- ディスクキャッシュ（同じ名前を再利用）
- odai ゲームでのコール再生
- BGM とのミックス
- 多言語対応
- プロンプトのユーザーカスタマイズ
- ElevenLabs 等他プロバイダ対応
