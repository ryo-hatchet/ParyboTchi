# nomiboy 設計仕様書

**日付**: 2026-04-26
**ステータス**: ブレインストーミング完了 / 実装計画待ち
**対象**: Raspberry Pi Zero 2 + 3.5" SPIタッチディスプレイ + Adafruit SPEAKER BONNET 上で動作する飲みゲー集合機

---

## 1. 概要

「nomiboy」は飲み会向けの携帯ゲーム機型プロトタイプ。タイトル画面 → ゲーム選択 → 個別ゲーム のシンプルな構成で、複数の飲みゲーを切り替えて遊べる。ゲームボーイカラー（GBC）風のレトロなビジュアルで、タッチパネルから操作する。

PC（macOS/Linux/Windows）でも同一コードで動作するため、ハード無しで開発・デバッグできる。

## 2. ハードウェア構成

| 要素 | 内容 |
|---|---|
| 本体 | Raspberry Pi Zero 2（メモリ 512MB） |
| ディスプレイ | 3.5インチ SPI タッチディスプレイ 480×320（横持ち） |
| 音声 | Adafruit SPEAKER BONNET（I2S DAC + アンプ + スピーカー） |
| 入力 | タッチパネルのみ（MVP） |
| ネットワーク | Wi-Fi（Gemini TTS 用、未接続でもゲームは動作可能） |

## 3. 要件サマリ

ヒアリングで決定した内容：

| 項目 | 決定内容 |
|---|---|
| ゲーム数（MVP） | 3本：爆弾タイマー / ルーレット / ○○な人は飲む |
| プレイヤー数 | 2〜4人 |
| プレイヤー登録 | タイトル画面で1回（A1）。フルキーボード（ひらがな・カタカナ・英数字）。起動ごとにリセット |
| 入力方式 | タッチのみ |
| 音 | 効果音 + BGM + Gemini TTS 読み上げ |
| 実装言語 | Python + Pygame |
| ビジュアル | GBC カラフル風（レトロ・ポップ） |
| 起動方式 | systemd で自動起動（Pi） |
| デザインドキュメント | 既存 Superhuman 風 `DESIGN.md` を `DESIGN.legacy.md` にアーカイブし、GBC 用 `DESIGN.md` を新規作成 |
| 各ゲームの細部仕様 | 最小仕様のみ本書に記載、後で詰める |

## 4. 全体アーキテクチャ

### 4.1 レイヤー構造

```
┌─────────────────────────────────────────────┐
│  Scenes（画面ごと）                          │
│   TitleScene / PlayerRegisterScene /         │
│   KeyboardScene / GameSelectScene /           │
│   BombScene / RouletteScene / OdaiScene /    │
│   ResultScene                                │
├─────────────────────────────────────────────┤
│  SceneManager（stack push/pop で遷移）        │
├─────────────────────────────────────────────┤
│  Core サービス（DI で Scene に注入）           │
│   InputAdapter / AudioService / TTSService /  │
│   PlayerStore / AssetLoader / Config          │
├─────────────────────────────────────────────┤
│  Pygame + ハード I/O                         │
│   - PC: 480×320 ウィンドウ + マウス           │
│   - Pi: SPI タッチディスプレイ全画面          │
└─────────────────────────────────────────────┘
```

**設計原則：**
- Scene は Core サービスを依存注入で受け取り、Core の実体に依存しない（テスト時はフェイクに差し替え可能）
- 入力は `InputAdapter` でタッチイベントとマウスイベントを統一の `InputEvent` に正規化（PCデバッグの要）
- ハード差分は `Config.IS_PI` 1箇所で判定し、各レイヤーへ伝搬

### 4.2 画面遷移フロー

```
[起動]
   ↓
[Title]──tap──→[PlayerRegister 0/4]
                        │
                        ├─ +追加 → [Keyboard] → 確定 → [PlayerRegister N/4]
                        │
                        └─ 開始（≥2人） → [GameSelect]
                                                 │
                                    ┌────────────┼────────────┐
                                    ↓            ↓            ↓
                                 [Bomb]    [Roulette]      [Odai]
                                    │            │            │
                                    ↓            ↓            ↓
                                [Result]    [Result]    （Result を経由しない、
                                    │            │       「終わる」で直接戻る）
                                    └────────────┴────────────┘
                                                 ↓
                                           [GameSelect]
```

- 各シーン左上に「← BACK」ボタンを配置し、`SceneManager.pop()` で前に戻る
- `GameSelect` から「タイトルへ戻る」を選ぶと確認ダイアログ → `reset_to(TitleScene)` でプレイヤーリセット
- **Bomb / Roulette** は1人の「ハズレ」が出るので Result 画面で発表 → tap で GameSelect へ
- **Odai** は全員飲むタイプで Result 不要。「次へ」で別のお題、「終わる」で GameSelect へ

## 5. ファイル構成

```
nomiboy/
├── DESIGN.md                  # GBC 風デザインガイド（新規）
├── DESIGN.legacy.md            # Superhuman 風（旧、参照用）
├── README.md
├── requirements.txt
├── pyproject.toml             # ruff/pytest 設定
├── .env.example               # GEMINI_API_KEY 等のテンプレ
│
├── src/nomiboy/
│   ├── __init__.py
│   ├── main.py                # エントリーポイント・引数解釈
│   ├── app.py                 # AppContext + メインループ + 例外フェイルセーフ
│   ├── config.py              # 解像度 / IS_PI 判定 / 環境変数
│   ├── colors.py              # GBC パレット定数
│   │
│   ├── core/
│   │   ├── scene.py           # Scene 抽象基底クラス
│   │   ├── scene_manager.py   # スタック管理 + 遷移
│   │   ├── input_adapter.py   # タッチ/マウス → InputEvent 統一
│   │   ├── audio_service.py   # BGM + SE
│   │   ├── tts_service.py     # Gemini TTS + キャッシュ
│   │   ├── asset_loader.py
│   │   └── widgets/
│   │       ├── button.py
│   │       ├── keyboard.py    # 50音 / カナ / 英数字 切替
│   │       └── text.py        # ピクセルフォント描画
│   │
│   ├── stores/
│   │   └── player_store.py
│   │
│   ├── scenes/
│   │   ├── title.py
│   │   ├── player_register.py
│   │   ├── keyboard_input.py
│   │   ├── game_select.py
│   │   └── result.py
│   │
│   └── games/
│       ├── __init__.py        # GameMeta 一覧（GameSelect で使う）
│       ├── bomb.py
│       ├── roulette.py
│       └── odai.py
│
├── assets/
│   ├── fonts/                 # 例: PressStart2P, k8x12 等のピクセルフォント
│   ├── images/
│   ├── sfx/                   # 効果音 .wav
│   ├── bgm/                   # BGM .ogg
│   └── tts_cache/             # Gemini TTS の永続キャッシュ
│
├── data/
│   └── odai_cards.json
│
├── tests/
│   ├── conftest.py            # SDL_VIDEODRIVER=dummy をセット
│   ├── test_player_store.py
│   ├── test_scene_manager.py
│   ├── test_input_adapter.py
│   ├── test_keyboard_widget.py
│   └── games/
│       ├── test_bomb.py
│       ├── test_roulette.py
│       └── test_odai.py
│
└── scripts/
    ├── run_pc.sh              # PC 開発用起動
    ├── run_scene.py           # 単一シーン起動デバッグツール
    └── install_pi.sh          # Pi セットアップ + systemd ユニット配置
```

## 6. 主要モジュール仕様

### 6.1 Core

**`app.py` AppContext**
- Core サービスを保持するコンテナ。`SceneManager` 経由で全 Scene の `on_enter(ctx)` に渡される
- 保有: `input_adapter` / `audio` / `tts` / `players` / `assets` / `config` / `online: bool`
- メインループ（`run()`）と Scene 例外フェイルセーフ（10.3 参照）もここに置く

**`core/scene.py`**

```python
class Scene(Protocol):
    def on_enter(self, ctx: AppContext) -> None: ...
    def on_exit(self) -> None: ...
    def handle_event(self, event: InputEvent) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
```

**`core/scene_manager.py`**
- `push(scene)` / `pop()` / `replace(scene)` / `reset_to(scene)`
- 空スタック時の `pop()` は `TitleScene` へフォールバック

**`core/input_adapter.py`**
- pygame の `MOUSEBUTTONDOWN` / `MOUSEBUTTONUP` / `MOUSEMOTION` / `FINGERDOWN` / `FINGERUP` / `FINGERMOTION` を統一の `InputEvent(kind: TAP|RELEASE|DRAG, x: int, y: int)` に変換
- 座標は常に画面ピクセル単位（pygame の touch event は 0.0〜1.0 の正規化座標なので、ここで `screen_size` を掛ける）

**`core/audio_service.py`**
- `play_se(name: str)` / `play_bgm(name: str, loop: bool = True)` / `stop_bgm()` / `set_master_volume(0.0〜1.0)`
- pygame.mixer ベース、ALSA バックエンドは pygame が吸収

**`core/tts_service.py`**
- `speak(text: str, voice: str = "default") → Path | None`（同期、戻り値は WAV パス、失敗時 None）
- キャッシュキー = `sha1(text + voice)`、保存先 `assets/tts_cache/{key}.wav`
- WiFi 未接続時：キャッシュにあれば返す、なければ `None`
- 例外は内部で握りつぶしログ出力（Scene へ伝播させない）

### 6.2 ウィジェット

**`core/widgets/keyboard.py`**
- 50音タブ / カナタブ / 英数字タブの切替トグル
- 確定ボタンで上位コンポーネントにコールバック
- 最大文字数 8（Player.name の上限）

### 6.3 ストア

**`stores/player_store.py`**
- `players: list[Player]`、最大4人、最小2人で開始可能
- `add(name)` / `remove(idx)` / `clear()`
- `Player.color` は登録順にパレットから自動割当（4色固定ローテーション）

### 6.4 ゲーム（最小仕様）

実装時に詰める前提で、本書では以下の最小仕様のみ記録：

**`games/bomb.py` 爆弾タイマー**
- ランダム秒（10〜30秒）でカウントダウン、画面に爆弾アイコン
- 「次へパス」ボタンでプレイヤー間を回す
- タイマー切れ時の保有者がハズレ → Result 画面で `「{name} は飲む！」`

**`games/roulette.py` ルーレット**
- 登録プレイヤー名がぐるぐる回る演出
- タップ or 自動停止でランダムに1名選出
- Result 画面で `「{name} は飲む！」`

**`games/odai.py` ○○な人は飲む**
- `data/odai_cards.json` から1枚ランダム抽出（直近 N 枚は除外）
- 画面に大きくテキスト表示、TTS で読み上げ
- 「次へ」で別のお題、「終わる」で GameSelect へ

## 7. データモデル

```python
@dataclass(frozen=True)
class Player:
    id: int
    name: str                          # 最大8文字
    color: tuple[int, int, int]

@dataclass(frozen=True)
class GameMeta:
    key: str                           # "bomb" / "roulette" / "odai"
    title: str                         # 表示名「ばくだんゲーム」等
    icon: str                          # アセットファイル名
    min_players: int
    max_players: int

@dataclass(frozen=True)
class OdaiCard:
    id: str
    text: str                          # 「最近一番遅くまで起きていた人」
```

`data/odai_cards.json` 形式:
```json
[
  {"id": "01", "text": "最近一番遅くまで起きていた人"},
  {"id": "02", "text": "今日一番おしゃれな人"}
]
```
MVP では 30 枚程度を同梱。

## 8. PC デバッグ戦略

### 8.1 ハード判定

`config.py` で起動時に1度だけ判定：

```python
IS_PI = (
    Path("/sys/firmware/devicetree/base/model").exists()
    and "Raspberry Pi" in Path("/sys/firmware/devicetree/base/model").read_text()
)
SCREEN_SIZE = (480, 320)
FULLSCREEN = IS_PI
HIDE_CURSOR = IS_PI
```

環境変数で上書き可能：`NOMIBOY_FULLSCREEN=0`、`NOMIBOY_FORCE_PI=1`（ハード再現テスト用）。

### 8.2 マウス＝タッチ

`InputAdapter` で正規化するため、Mac ではマウスクリックがタップに、ドラッグがフリックに対応する。Scene 側は入力源を意識しない。

### 8.3 単一シーン起動

`scripts/run_scene.py <scene_name> [--players "あ,い,う"]` で任意の Scene を直接起動。スクリーンショット取得・特定シーンのデバッグに使う。

### 8.4 起動コマンド

| 用途 | コマンド |
|---|---|
| Mac で開発 | `./scripts/run_pc.sh`（= `python -m nomiboy --windowed`） |
| Mac で単一シーン | `python scripts/run_scene.py odai` |
| Pi で手動起動 | `python -m nomiboy` |
| Pi 自動起動 | systemd: `nomiboy.service`（`scripts/install_pi.sh` で配置） |

### 8.5 ログ

`logging` モジュールで `~/.nomiboy/log.txt` に日次ローテーション。Pi の SD カード保護のため INFO レベル以上のみ。

## 9. テスト戦略

### 9.1 対象範囲

| レイヤー | テスト | しない |
|---|---|---|
| `stores/player_store` | 追加/削除/クリア、最大4人制限 | — |
| `core/scene_manager` | push/pop/replace、空スタック時の挙動 | — |
| `core/input_adapter` | pygame イベント → InputEvent 変換 | — |
| `core/widgets/keyboard` | 文字確定、モード切替 | — |
| `games/bomb` | タイマー進行、爆発判定、パス処理 | 描画 |
| `games/roulette` | 抽選確率、停止判定 | 描画 |
| `games/odai` | カードランダム抽出、重複回避 | 描画 |
| Scene の `draw()` | — | 画面比較は行わない |

### 9.2 土台

- `pygame.init()` を伴うテストは `conftest.py` で `os.environ["SDL_VIDEODRIVER"] = "dummy"` をセットしてヘッドレス実行
- `TTSService` / `AudioService` はテスト時 `FakeTTSService` / `FakeAudioService` に差し替え（DI）
- 乱数を伴うロジック（ルーレット・お題）は `random.Random(seed)` を受け取れる形にして決定論的テスト

### 9.3 カバレッジ目標

stores・core・games のロジック層で 70% 以上。描画は対象外。

## 10. エラーハンドリング・ネットワーク

### 10.1 WiFi 未接続検出

- 起動時に Gemini エンドポイントへ HEAD リクエスト（5秒タイムアウト） → 失敗時 `AppContext.online = False`
- タイトル画面右上に既存パターン踏襲で「📡 OFFLINE」赤文字バッジを表示
- ゲームプレイは全てオフラインで完結。TTS は拡張機能扱い

### 10.2 Gemini TTS エラー

- タイムアウト 5秒、リトライ1回、失敗時はキャッシュフォールバックまたは無音
- 例外は `tts_service` 内で捕捉してログのみ。Scene 側に伝播させずゲームを止めない

### 10.3 致命的エラー

- 画面に「💥 エラーが発生しました」を5秒表示してタイトルへ戻る（Scene 例外を `app.py` でキャッチ）
- ログに stack trace を残し、Pi では loop で再起動 → systemd の `Restart=on-failure` が拾う

### 10.4 データファイル欠損

- `data/odai_cards.json` 読み込み失敗 → コード内に同梱したフォールバック5枚を使用

## 11. 性能ターゲット（Pi Zero 2 想定）

| 指標 | 目標 |
|---|---|
| 起動から Title 表示 | 5秒以内 |
| Scene 遷移 | 200ms 以内 |
| FPS | 30 fps 以上維持 |
| メモリ常駐 | 100MB 以内 |

達成のため：Pygame の `Surface` 事前ロード、フォントレンダリング結果のキャッシュ、毎フレームのメモリ alloc を避ける。

## 12. 後で詰める項目（オープン）

実装フェーズで詳細を決める：

- 各ゲームのゲーム性（爆弾の演出、ルーレットの停止アルゴリズム、お題のジャンル分類）
- GBC 風カラーパレット・フォントの正式な選定（`DESIGN.md` 新規作成時に決定）
- BGM / SE のアセット調達（フリー素材 or 自作）
- Gemini TTS の音声バリエーション（プレイヤー名読み上げの抑揚など）
- 物理ボタン拡張（MVP 後の検討課題）
- Pi 起動時のスプラッシュ画面

## 13. 参考

- 同リポジトリ内 `ParyboTchi/` — 同じハード構成（Pi + SPIディスプレイ + I2S スピーカー）の Python/Pygame 前例
- `nomiboy/DESIGN.legacy.md` — 旧 Superhuman 風デザインドキュメント（参照用）
