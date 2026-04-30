# ロシアン飲酒（Russian Tap）設計書

- ステータス: 承認済み（2026-05-01 ブレストで合意）
- 親仕様: `2026-04-26-nomiboy-design.md`
- 実装計画: 別途作成予定（writing-plans スキル）

## 概要

3×3 = 9マスの盤面に爆弾を1マスだけ隠し、プレイヤーが順番に1マスずつタップ。爆弾を引いた人が一気飲み、というシンプルな飲み会用ロシアンルーレット型ゲーム。タッチ画面の「マスを選んで指で引きに行く」操作感を活かし、運命感と煽り合いで盛り上がることを狙う。

## 配置するファイル

| 種類 | パス | 内容 |
|---|---|---|
| 新規 | `src/nomiboy/games/russian_tap.py` | `RussianTapController` + `RussianTapScene` |
| 新規 | `tests/games/test_russian_tap.py` | コントローラの pytest テスト |
| 編集 | `src/nomiboy/games/__init__.py` | `GAME_META` にロシアン飲酒を追加・`GameMeta.icon` を `Optional[str]` に |
| 編集 | `src/nomiboy/scenes/game_select.py` | 2×2 グリッド + ページング機構に書き換え + `_launch` 分岐追加 |
| 編集 | `tests/test_scene_manager.py` 周辺 | GameSelect ページングテストの新規追加（別ファイルでも可） |

## ゲーム設計（コアループ）

1. **準備**：プレイヤー登録は既存 `PlayerRegisterScene` を流用。対応人数 2〜8人。
2. **盤面生成**：`RussianTapController.start()` で
   - 9マスのうち1マスにランダムで爆弾を配置（位置はプレイヤーに非表示）
   - 先攻プレイヤーをランダムに決定
3. **ターン進行**：
   - 自分の番のプレイヤーが空いているマスを1つタップ
   - **セーフ**：そのマスを `safe_cells` に追加（× 印で無効化）→ 次プレイヤーへ `(i+1) % n`
   - **爆弾**：`exploded=True`、`loser_index` を確定 → 演出後 `ResultScene` へ
4. **再戦**：`ResultScene` から戻ると `GameSelectScene` に遷移（既存挙動）

### 仕様パラメータ

| パラメータ | 値 |
|---|---|
| 盤面 | 3×3 = 9マス |
| 爆弾の数 | 1個（固定） |
| パス | なし（必ず1マス選ぶ） |
| 先攻決定 | ランダム抽選 |
| ターン進行 | 登録順右回り |
| 対応人数 | 2〜8人 |

## RussianTapController（純ロジック）

```python
class RussianTapController:
    BOARD_SIZE: int = 9  # 3×3

    def __init__(self, player_count: int, rng: random.Random | None = None) -> None: ...

    @property
    def current_player_index(self) -> int: ...
    @property
    def safe_cells(self) -> set[int]: ...        # 既にタップ済みセーフマス
    @property
    def exploded(self) -> bool: ...
    @property
    def loser_index(self) -> int | None: ...     # 爆発後のみ非None

    def start(self) -> None:
        """爆弾位置と先攻をランダム決定。"""

    def tap(self, cell_index: int) -> bool:
        """指定マスをタップ。
        戻り値: 爆弾なら True、セーフなら False。
        - 爆発後 / 既タップマス / 範囲外 cell_index は no-op で False を返す。
        """
```

- `BombController` と同じく `rng` を注入できる設計（再現性のあるテスト用）
- `tap()` の no-op パスは戻り値 `False`、状態変更なし

## RussianTapScene（描画＋入力）

`BombScene` のパターンを踏襲：
- `on_enter`：Controller 初期化、9マスの `pygame.Rect` 配列を生成、BACK ボタン配置
- `handle_event`：タップ位置から cell_index を計算（マス Rect の `collidepoint`）→ `ctrl.tap()`
- `update`：爆発演出タイマー（`_explosion_timer`）を進め、終了したら `ResultScene` を push
- `draw`：上部プレイヤー帯 + 9マス + 爆発演出

### 画面レイアウト（480×320）

```
┌─────────────────────────────────────────────┐  y=0
│ [BACK]            ○○ の ばん！           │  y=0..50  ← 現在プレイヤー帯（プレイヤー色背景）
├─────────────────────────────────────────────┤  y=50
│                                             │
│        ┌───┐ ┌───┐ ┌───┐                  │
│        │ ? │ │ × │ │ ? │   ← 3×3 グリッド │
│        └───┘ └───┘ └───┘   72×72px        │  y=70..310
│        ┌───┐ ┌───┐ ┌───┐   gap=12px       │
│        │ × │ │ ? │ │ ? │                   │
│        └───┘ └───┘ └───┘                   │
│        ┌───┐ ┌───┐ ┌───┐                   │
│        │ ? │ │ ? │ │ ? │                   │
│        └───┘ └───┘ └───┘                   │
│                                             │
└─────────────────────────────────────────────┘  y=320
```

- 上部 50px：現在プレイヤー名（プレイヤー色を背景に）
- 中央 3×3 グリッド：マス 72×72、間隔 12px、中央寄せ
  - 横：72×3 + 12×2 = 240、左右余白 (480 − 240) / 2 = **120px**
  - 縦：上部帯 50px + 上余白 20px = y=70 から開始、72×3 + 12×2 = 240 → y=310 で終わり、下余白 10px

### マス状態の色分け

| 状態 | 背景 | 表記 |
|---|---|---|
| 未タップ | `BG_SECONDARY`（オレンジ） | `?` |
| セーフ済み | グレー | `×` |
| 爆弾発覚（演出中） | `DANGER_RED` | `BOOM` |

### 演出

| イベント | 演出 |
|---|---|
| ターン切替 | 上部の名前が次プレイヤーの色に即切替 |
| セーフタップ | マスを `×` にしてグレー化 |
| 爆弾タップ | 画面全体を赤フラッシュ（3回点滅、約 0.6 秒）→ 中央に大きく `BOOM` → `ResultScene` へ |
| 結果発表 | 既存 `ResultScene` を流用。`ctx.tts.speak("○○ は飲む！")` も既存通り発火 |

### TTS 利用方針

- ゲーム中は TTS を **使わない**（テンポ重視、ターンごとに喋らない）
- 爆発後の `ResultScene` でのみ TTS（既存挙動を維持）
- オフラインでも全機能が動く

### 効果音（SE）

- MVP では SE なし（無音 + ビジュアル演出のみ）
- 爆発音 SE は将来追加可（`assets/` への音源配置が必要）

## GameSelectScene の改修（ページング対応）

### 改修方針

将来ゲームが増えていくことを前提に、ゲーム選択画面に **ページング機構** を導入する。

### レイアウト

```
┌────────────────────────────────────┐
│ [TITLE]      SELECT GAME           │
│                                    │
│   ┌───────┐  ┌───────┐            │
│   │ BOMB  │  │ROULETTE│           │
│   └───────┘  └───────┘            │
│   ┌───────┐  ┌───────┐            │
│   │ ODAI  │  │ロシアン│   <  >    │ ← 5ゲーム以上で右下にページ送り
│   │       │  │ 飲酒   │            │
│   └───────┘  └───────┘            │
│         ・ ●  (ページインジケータ) │
└────────────────────────────────────┘
```

### 仕様

- 1ページ = 2×2 = 最大4ゲーム
- ゲーム数が4以下 → 矢印・インジケータ非表示（現行 4 ゲームでは矢印は出ない）
- ゲーム数が5以上 → 右下に `<` `>` ボタン、下中央にページインジケータ
- 5ゲーム目を追加した瞬間から自動的にページング開始
- スワイプ操作は MVP 外（タップのみ）。`InputAdapter` 自体は DRAG を吐けるので将来追加可能

### ボタンサイズ

- 130×130（現行と同等）。ラベル「ロシアン飲酒」は 12pt フォントで横72px ≒ ボタン内に収まる想定。実装で再確認。

## GAME_META 更新

```python
GameMeta(key="russian_tap", title="ロシアン飲酒", icon=None, min_players=2, max_players=8),
```

- `GameMeta.icon` を `Optional[str]` に変更（既存3件のアイコンも実体不明なので、ここで Optional 化）
- 新規ゲームはアイコン無しで開始、テキスト中心の表示

## `_launch` の分岐追加

```python
elif key == "russian_tap":
    from nomiboy.games.russian_tap import RussianTapScene
    self._sm.push(RussianTapScene(self._sm))
```

## テスト方針

### `tests/games/test_russian_tap.py`

| # | ケース | 検証内容 |
|---|---|---|
| 1 | `test_start_initializes_state` | `start` 後、`exploded=False`、`safe_cells` 空、`loser_index is None`、`current_player_index ∈ [0, n)` |
| 2 | `test_bomb_position_is_random_but_reproducible` | 同じ seed の rng で2回 start → 爆弾位置が同じ |
| 3 | `test_first_player_is_random_but_reproducible` | 同上で先攻が同じ |
| 4 | `test_safe_tap_adds_cell` | セーフマスタップ → `safe_cells` に含まれる、`exploded=False` |
| 5 | `test_safe_tap_advances_player` | セーフタップで `current_player_index` が `(i+1) % n` |
| 6 | `test_bomb_tap_explodes` | 爆弾マスタップ → `exploded=True`、`loser_index` = タップしたプレイヤー |
| 7 | `test_double_tap_same_cell_is_noop` | 既タップマス再タップで状態不変 |
| 8 | `test_tap_after_explosion_is_noop` | 爆発後のタップで状態不変、`current_player_index` 不変 |
| 9 | `test_invalid_cell_index_is_noop` | `tap(-1)` / `tap(9)` で例外なし、状態不変 |
| 10 | `test_bomb_position_uniformly_distributed` | seed を 1000 通り変えて start → 各マスへの爆弾配置回数がカイ二乗検定で一様（`test_roulette.py` と同手法） |
| 11 | `test_turn_cycles_through_players` | 3人で 3 回セーフタップ → `current_player_index` が `start → (start+1)%3 → (start+2)%3 → start` と一巡する（先攻が何であっても循環することを検証） |

### `GameSelectScene` のページングテスト

新規ファイル `tests/test_game_select_paging.py`（or 既存 `test_scene_manager.py` に統合）に以下を追加：

| # | ケース | 検証内容 |
|---|---|---|
| 1 | `test_no_paging_when_4_or_fewer_games` | ゲーム数 ≤ 4 で矢印非表示 |
| 2 | `test_paging_shown_when_5_or_more` | ゲーム数 ≥ 5 で `<` `>` 表示 |
| 3 | `test_next_page_advances` | `>` タップで `current_page` が +1 |
| 4 | `test_prev_page_disabled_on_first` | 1ページ目で `<` は無効 |
| 5 | `test_next_page_disabled_on_last` | 最終ページで `>` は無効 |
| 6 | `test_page_indicator_count_matches_pages` | インジケータの個数 = 総ページ数 |

### スコープ外

- `RussianTapScene` の描画テスト（既存ゲームも書いていない）
- 爆発演出のフレーム単位テスト

## マイルストーン / 完了条件

- [ ] `RussianTapController` 実装＋11ケース全てパス
- [ ] `RussianTapScene` 実装＋PC でデバッグ起動して1ラウンド遊べる
- [ ] `GameSelectScene` 改修＋6ケース全てパス
- [ ] `GAME_META` に追加、`GameMeta.icon` Optional 化に伴う既存参照の追従
- [ ] PC 起動 (`./scripts/run_pc.sh`) で `ロシアン飲酒` を選んで爆発まで遊べる
- [ ] `pytest -v` で既存テスト含め全パス

## YAGNI（やらないこと）

- 爆弾を複数個にする / 盤面サイズ変更（3×3 固定）
- スワイプ操作によるページ送り
- 効果音（爆発 SE 等）
- ゲーム中の TTS 読み上げ
- 既存ゲーム名（BOMB/ROULETTE/ODAI）の日本語化
- 6ゲーム目以降のための柔軟な行列計算（4個まで2×2で固定）
