# 飲みゲーカラオケ ゲーム設計

> ステータス: 設計確定 / 2026-05-31 ブレスト承認済
> 関連: ドリンクコール spec (2026-05-29) と同じ Lyria 3 / Gemini インフラを再利用

## 目的

プレイヤー名入りで毎回違うジャンルの「やばいカラオケ曲」を生成し、全員で聴いて飲み会を盛り上げる。勝ち負け無し、ただ流すだけ。

## ゴール / 非ゴール

### ゴール
- KARAOKE をゲーム選択 → 1 曲生成 → 全員で聴く → 乾杯シーン → GameSelect 復帰
- 歌詞: 全員の名前を**不均衡**に含める（一部に集中、一部は控えめ）
- ジャンル: 毎回ランダム（ヘビーメタル / ロック / アイドル / 昭和歌謡 / J-POP / EDM / 演歌 / ヒップホップ）
- サビで「乾杯！」コールを全員で
- 歌詞は **毎回 Gemini Flash で生成**してから Lyria 3 Pro に渡す
- 生成中はプログレスバー表示（~30 秒）
- 再生中は歌詞テロップ風スクロール

### 非ゴール
- 個別スコア / 採点（YAGNI）
- 録音 / 歌唱判定
- 連続再生モード（毎回 GameSelect 戻り）
- 歌詞の時間同期表示（行を均等割で送る簡易表示で代用）
- Pi 以外での録音機能（カラオケなので無音でもよい）

## 全体像

```
[GameSelect] → KARAOKE タップ → push(KaraokeScene)
   │
   ▼
[KaraokeScene: GENERATING] 30 秒程度
   │  ┌─ Gemini Flash で歌詞生成（並列）
   │  └─ 完了次第 Lyria 3 Pro に投げて楽曲生成
   ▼
[KaraokeScene: PLAYING] mixer.music 再生 + 歌詞行送り
   │
   ▼ 曲終了 / タイマー
[KaraokeScene: KANPAI] 「乾杯！」2 秒
   │
   ▼ pop
[GameSelect]  ← pop で復帰、コール音停止 (Result と同じパターン)
```

## コンポーネント

### `core/lyrics_service.py` 新規

```python
class LyricsService:
    def __init__(
        self,
        api_key: str | None,
        model: str = "gemini-3.5-flash",
        timeout_sec: float = 15.0,
    ) -> None: ...

    def generate_song_lyrics(
        self,
        genre: str,
        emphasis: dict[str, float],  # 名前 -> 0.1~1.0 のコール度
    ) -> str | None:
        """Lyrics: タグ付きの歌詞テキストを返す。失敗時 None。"""
```

プロンプト構造:
```
あなたは飲み会用カラオケソングの作詞家。
ジャンル: {genre}
出演者の名前と「コール度」（高いほど名前を多く入れる）:
- たろう: 0.9
- はなこ: 0.4

ルール:
- [Intro][Verse 1][Chorus][Verse 2][Outro] 構成
- 名前はコール度に比例した頻度で登場
- [Chorus] に必ず「乾杯！」を入れる
- 飲み会らしいノリ、合計 20 秒程度の歌詞

以下の形式で返答:
Lyrics:
[Intro]
...
```

レスポンスは plain text。安全フィルタ等で空応答なら None。

### `core/lyria_service.py` 拡張

既存 `synthesize_call(player_name, template)` はそのまま残す。

新規追加:
```python
def synthesize_song(self, prompt: str, duration_sec: int = 20) -> bytes | None:
    """任意プロンプトで楽曲生成。Style + Duration + Lyrics を含む完全プロンプト想定。"""
```

`_generate` を共通化して `_call_lyria(prompt: str) -> bytes | None` に抽出するリファクタも入れる。

### `games/karaoke.py` 新規

```python
class KaraokeState(Enum):
    GENERATING = "generating"
    PLAYING = "playing"
    KANPAI = "kanpai"

class KaraokeScene:
    show_menu = True

    def __init__(self, scene_manager) -> None: ...
    def on_enter(self, ctx) -> None:
        # ジャンルランダム選択
        # コール度をプレイヤーごとにランダム生成 (0.1~1.0)
        # Gemini で歌詞生成 → Lyria で楽曲生成 を別スレッドで起動
        # state = GENERATING
    def on_exit(self) -> None:
        # mixer.music.stop()
    def handle_event(self, event) -> None:
        pass  # 期間中タップ無視（MENU だけ反応）
    def update(self, dt) -> None:
        # state 遷移管理
    def draw(self, surface) -> None:
        # state ごとに描画
```

状態機械:
- `GENERATING`: 生成中スピナー + プログレスバー + ジャンル名表示。タイムアウト 60 秒
- `PLAYING`: mixer.music で再生開始、歌詞を上→下にスクロール
- `KANPAI`: 「乾杯！」表示 2 秒

### `data/karaoke_genres.json` 新規

```json
["ヘビーメタル", "J-POP", "昭和歌謡", "アイドルソング", "EDM", "ロック", "演歌", "ヒップホップ"]
```

### `games/__init__.py` 修正

```python
GameMeta(key="karaoke", title="カラオケ", icon=None, min_players=2, max_players=8),
```

### `scenes/game_select.py` 修正

`_launch` の dispatch に karaoke を追加:
```python
if key == "karaoke":
    from nomiboy.games.karaoke import KaraokeScene
    return lambda sm: KaraokeScene(sm)
```

### `config.py` 追加

```python
KARAOKE_GENRES_PATH = DATA_DIR / "karaoke_genres.json"
LYRICS_MODEL = "gemini-3.5-flash"
LYRICS_TIMEOUT_SEC = 15
KARAOKE_DURATION_SEC = 20
KARAOKE_GENERATE_TIMEOUT_SEC = 60
KARAOKE_KANPAI_SEC = 2.0
```

### `app.py` 修正

`AppContext` に `lyrics: LyricsService` を追加して初期化。

## データフロー

```
[Karaoke on_enter]
  ├ genre = random.choice(GENRES)
  ├ emphasis = {p.name: random.uniform(0.1, 1.0) for p in players}
  ├ ThreadPoolExecutor で start_background_generation()
  │    ├ lyrics = lyrics_service.generate_song_lyrics(genre, emphasis)
  │    └ song_bytes = lyria_service.synthesize_song(
  │           style + duration_sec + lyrics
  │       )
  └ state = GENERATING, _t = 0

[Karaoke update (per frame)]
  ├ if state == GENERATING:
  │    _t += dt
  │    if future.done():
  │        result = future.result()
  │        if result:
  │            (lyrics, song_path) = result   # tempfile 経由
  │            mixer.music.load(song_path); mixer.music.play()
  │            state = PLAYING; _t = 0
  │            _lyric_lines = parse_lyrics(lyrics)
  │        else:
  │            state = KANPAI  # 失敗、即終了
  │    elif _t > KARAOKE_GENERATE_TIMEOUT_SEC:
  │        state = KANPAI
  ├ elif state == PLAYING:
  │    _t += dt
  │    if not mixer.music.get_busy() or _t > KARAOKE_DURATION_SEC + 20:
  │        state = KANPAI; _t = 0
  └ elif state == KANPAI:
       _t += dt
       if _t >= KARAOKE_KANPAI_SEC:
            self._sm.pop()

[Karaoke draw]
  state == GENERATING: ジャンル名 + プログレスバー (_t / 30)
  state == PLAYING:    ジャンル名 + 歌詞行送り (_t / duration)
  state == KANPAI:     「乾杯！」中央表示 + ビールジョッキ
```

## UI 詳細

### GENERATING (480×320)

```
┌────────────────────────────────────────┐
│                                MENU →   │
│  🎤 カラオケ生成中…                     │
│                                        │
│        ジャンル: ヘビーメタル            │
│                                        │
│   [▓▓▓▓▓▓░░░░░░░░░░░░░░░]              │
│                  12s / 30s              │
│                                        │
│        🍺                              │
└────────────────────────────────────────┘
```

プログレスバー: `_t / 30.0`（30 秒の見積もり、超えても緩やかに伸ばす）

### PLAYING (480×320)

```
┌────────────────────────────────────────┐
│                                MENU →   │
│  ♪ ヘビーメタル                         │
│                                        │
│  たろう が今夜も飲み干す                │ ← 上から流れて
│  はなこ も乾杯しろ！                     │   下に消える
│  けんじ 一気！ 一気！                    │
│                                        │
│  [▓▓▓▓▓▓▓░░░░] 18s                    │
└────────────────────────────────────────┘
```

歌詞行送り: 全行数を曲の長さで均等割、_t に従って表示位置を進める。

### KANPAI (480×320)

```
┌────────────────────────────────────────┐
│                                        │
│         🍺   乾杯！   🍺                │
│                                        │
│       かんぱい！ かんぱい！             │
│                                        │
│         (ビールジョッキ大)               │
│                                        │
└────────────────────────────────────────┘
```

`game_start_intro.py` の `_draw_beer_mug` を再利用。

## エラー処理

| ケース | 動作 |
|---|---|
| `GEMINI_API_KEY` 未設定 | エントリ時にエラー表示 → 5 秒で pop |
| Gemini 歌詞生成失敗 (None / timeout) | デフォルト歌詞テンプレ (player names + "乾杯") で代用、続行 |
| Lyria 楽曲生成失敗 | エラー表示 → 即 KANPAI 飛び → pop |
| 楽曲タイムアウト (60 秒) | エラー表示 → 即 KANPAI 飛び → pop |
| ネット無し (`ctx.online == False`) | KARAOKE 起動時に「ネット必要」と表示 → 5 秒で pop |
| 再生中に MENU タップ | 既存 MenuOverlay の挙動（BACK TO TITLE / SELECT GAMES）。on_exit で mixer.music 停止 |

## テスト

`tests/test_lyrics_service.py`
- API キー未設定 → None
- Gemini レスポンスを mock し正常系で Lyrics 文字列を返す
- 例外時 None

`tests/test_karaoke_scene.py`
- 状態遷移 (GENERATING → PLAYING → KANPAI → pop)
- 生成タイムアウトで KANPAI に飛ぶ
- 歌詞行のパース（[Intro] [Verse] [Chorus] でセクション分割）

## 受け入れ条件

1. KARAOKE をゲーム選択でき、KaraokeScene が起動する
2. `GENERATING` 中はプログレスバーと「ジャンル: XX」が表示される
3. 約 30 秒以内に楽曲生成が完了して再生される
4. 再生中は歌詞行が上から下に流れる
5. 曲が終わると 2 秒「乾杯！」表示 → GameSelect に自動復帰
6. GameSelect 復帰時にコール音 (mixer.music) が確実に停止する
7. ネット切断 / API キー未設定でクラッシュしない

## スコープ外（将来）

- 録音とスコア
- 連続再生モード
- 歌詞のリアルタイム表示同期
- 個別プレイヤー solo モード
- Pi での USB マイク対応
- 歌詞編集 / 履歴保存
