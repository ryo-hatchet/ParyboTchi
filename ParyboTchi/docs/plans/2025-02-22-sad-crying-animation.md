# Sad Crying Animation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 24時間以上音楽を聴いていない場合の「怒り」エモーションを「悲しみ」エモーションに置き換え、`character_sad.jpeg` と `character_sad_crying.jpeg` を0.5秒間隔で交互に切り替えることで泣いているエフェクトを実現する。

**Architecture:** `angry` エモーションを完全に `sad` に置き換える。`Character` クラスに `sad_cry_timer` を追加し、`update()` で0.5秒ごとにフラグを切り替える。`_draw_image()` でフラグに応じて `sad` か `sad_crying` の画像を表示する。`config.py` と `main.py` も合わせて更新する。

**Tech Stack:** Python, pygame

---

### Task 1: config.py の更新

**Files:**
- Modify: `config.py`（`CHARACTER_IMAGES` 辞書）

**Step 1: `angry` を削除し `sad`・`sad_crying` を追加**

`config.py` の `CHARACTER_IMAGES` を以下に変更：

```python
CHARACTER_IMAGES = {
    "normal": os.path.join(ASSETS_DIR, "character_normal.jpeg"),
    "blink": os.path.join(ASSETS_DIR, "character_blink.jpeg"),
    "listening": os.path.join(ASSETS_DIR, "character_listening.jpeg"),
    "happy": os.path.join(ASSETS_DIR, "character_happy.jpeg"),
    "sad": os.path.join(ASSETS_DIR, "character_sad.jpeg"),
    "sad_crying": os.path.join(ASSETS_DIR, "character_sad_crying.jpeg"),
}
```

**Step 2: コミット**

```bash
git add config.py
git commit -m "設定: angryをsad/sad_cryingに置き換え"
```

---

### Task 2: character.py の更新

**Files:**
- Modify: `character.py`

**Step 1: `__init__` に泣きアニメ用タイマーを追加**

`Character.__init__()` 内の `self.emotion = "normal"` の行の後に追加：

```python
# 泣きアニメーション用タイマー（sad エモーション時に使用）
self._sad_cry_timer = 0.0
self._SAD_CRY_INTERVAL = 0.5  # sad ↔ sad_crying の切り替え間隔（秒）
self._show_crying = False  # False=sad, True=sad_crying
```

**Step 2: `update()` の瞬きロジックを修正**

`update()` 内の瞬き条件を `angry` → `sad` に変更：

```python
# 瞬きロジック（normal / listening / sad のときのみ）
if self.emotion in ("normal", "listening", "sad"):
```

**Step 3: `update()` に泣きアニメーション更新を追加**

瞬きロジックブロックの直後（`else:` ブロックの後）に追加：

```python
# 泣きアニメーション（sad のときのみ）
if self.emotion == "sad":
    self._sad_cry_timer += dt
    if self._sad_cry_timer >= self._SAD_CRY_INTERVAL:
        self._sad_cry_timer = 0.0
        self._show_crying = not self._show_crying
else:
    # sad 以外のときはリセット
    self._sad_cry_timer = 0.0
    self._show_crying = False
```

**Step 4: `_draw_image()` の表示ロジックを修正**

`_draw_image()` 内の画像選択ロジックを以下に変更：

```python
def _draw_image(self, surface, alpha=255):
    """画像で描画"""
    # sad のとき: sad ↔ sad_crying を交互表示
    if self.emotion == "sad":
        if self._show_crying and "sad_crying" in self._images:
            img = self._images["sad_crying"]
        else:
            img = self._images.get("sad", self._images.get("normal"))
    # 瞬き中はblinkを優先表示
    elif self.is_blinking and "blink" in self._images:
        img = self._images["blink"]
    else:
        img = self._images.get(self.emotion, self._images.get("normal"))
```

**Step 5: `_load_images()` のフォールバック修正**

`_load_images()` 内の `angry` フォールバックを `sad` / `sad_crying` に変更：

```python
# sad がなければ normal で代用
if "sad" not in self._images:
    self._images["sad"] = self._images["normal"]
# sad_crying がなければ sad → normal の順で代用
if "sad_crying" not in self._images:
    self._images["sad_crying"] = self._images.get(
        "sad", self._images["normal"])
```

**Step 6: `_draw_fallback()` の口の描画を修正**

`_draw_fallback()` 内の `angry` 条件を `sad` に変更：

```python
elif self.emotion == "sad":
    # への字口（悲しい）
    pygame.draw.arc(surface, (60, 60, 60),
                    (cx - 12, cy + 8, 24, 14), 0.2, 3.0, 2)
```

**Step 7: コミット**

```bash
git add character.py
git commit -m "キャラクター: sad泣きアニメーション実装（0.5秒間隔でsad↔sad_crying切り替え）"
```

---

### Task 3: main.py の更新

**Files:**
- Modify: `main.py`

**Step 1: `_check_angry_state()` を `_check_sad_state()` に変更**

メソッド名と内部の `angry` 参照をすべて `sad` に変更：

```python
def _check_sad_state(self):
    """24時間以上音楽を聴いていなければ悲しい状態にする"""
    hours = self.collection.hours_since_last_song()
    if hours >= ANGRY_THRESHOLD_HOURS:
        if self.character.emotion == "normal":
            print(f"[APP] 悲しみモード: 最後の曲から{hours:.1f}時間経過")
            self.character.emotion = "sad"
    else:
        # 24時間以内なら悲しみを解除（録音中・happy 中は上書きしない）
        if self.character.emotion == "sad":
            self.character.emotion = "normal"
```

**Step 2: `__init__` の呼び出しを更新**

```python
# 起動時に即チェック
self._check_sad_state()
```

**Step 3: `_handle_events()` の呼び出しを更新**

`USEREVENT + 1` のハンドラ内：

```python
elif event.type == pygame.USEREVENT + 1:
    # happy → normal に戻る（その後 24時間経過なら sad に切り替え）
    self.character.emotion = "normal"
    self._check_sad_state()
```

**Step 4: `_update()` の呼び出しを更新**

定期チェック部分：

```python
if self._angry_check_timer >= self._ANGRY_CHECK_INTERVAL:
    self._angry_check_timer = 0.0
    self._check_sad_state()
```

**Step 5: コミット**

```bash
git add main.py
git commit -m "メイン: angry→sadに置き換え、_check_sad_state()に変更"
```

---

### Task 4: assets フォルダに画像を配置確認

**Step 1: 画像ファイルの存在確認**

```bash
ls /Users/d21144/Documents/PrototypeProject/Yuengiken/ParyboTchi/assets/character_sad*.jpeg
```

Expected:
```
character_sad.jpeg
character_sad_crying.jpeg
```

もし assets/ に存在しない場合は、ユーザーが格納したフォルダから assets/ にコピーする。

**Step 2: 動作確認**

```bash
cd /Users/d21144/Documents/PrototypeProject/Yuengiken/ParyboTchi
python main.py
```

24時間経過のテストは `ANGRY_THRESHOLD_HOURS` を一時的に `0` にして確認する。
