# Dead State Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 72時間（3日）以上音楽を聴いていない場合にキャラクターが `dead` 状態になり、`character_dead.jpeg` を静止表示する。曲を認識できたら `happy` エフェクトで復活する。

**Architecture:**
状態遷移は `normal → (24h) → sad → (72h) → dead`。`dead` 状態でも録音は可能で、曲を認識できたら `happy` → `normal` に復活する。`_check_sad_state()` を `_check_emotion_state()` に拡張して dead 判定を追加する。

**Tech Stack:** Python, pygame

---

### Task 1: config.py の更新

**Files:**
- Modify: `config.py`

**Step 1: `dead` 画像と閾値定数を追加**

`CHARACTER_IMAGES` に `dead` を追加：
```python
CHARACTER_IMAGES = {
    "normal": os.path.join(ASSETS_DIR, "character_normal.jpeg"),
    "blink": os.path.join(ASSETS_DIR, "character_blink.jpeg"),
    "listening": os.path.join(ASSETS_DIR, "character_listening.jpeg"),
    "happy": os.path.join(ASSETS_DIR, "character_happy.jpeg"),
    "happy2": os.path.join(ASSETS_DIR, "character_happy2.jpeg"),
    "sad": os.path.join(ASSETS_DIR, "character_sad.jpeg"),
    "sad_crying": os.path.join(ASSETS_DIR, "character_sad_crying.jpeg"),
    "dead": os.path.join(ASSETS_DIR, "character_dead.jpeg"),
}
```

`ANGRY_THRESHOLD_HOURS` の下に追加：
```python
DEAD_THRESHOLD_HOURS = 72  # 最後に曲を聴いてからこの時間を超えると死亡
```

**Step 2: コミット**
```bash
git add config.py
git commit -m "設定: dead状態の画像・閾値(72h)を追加"
```

---

### Task 2: character.py の更新

**Files:**
- Modify: `character.py`

**Step 1: `_load_images()` に dead フォールバックを追加**

`sad_crying` フォールバックの後に追加：
```python
# dead がなければ sad → normal で代用
if "dead" not in self._images:
    self._images["dead"] = self._images.get(
        "sad", self._images["normal"])
```

**Step 2: `update()` のバウンスを dead 時は停止**

バウンス計算のブロックを修正：
```python
if self.emotion == "happy":
    self.bounce_offset = math.sin(self.bounce_timer * 7) * 4
elif self.emotion == "listening":
    self.bounce_offset = math.sin(self.bounce_timer * 3) * 2
elif self.emotion == "dead":
    self.bounce_offset = 0  # dead は静止
else:
    self.bounce_offset = math.sin(self.bounce_timer * 1.5) * 3
```

**Step 3: `update()` の瞬きロジックに dead を除外（already excluded since not in the tuple, but make it explicit）**

瞬き対象の条件はすでに `("normal", "listening", "sad")` なので dead は自動的に除外される。変更不要。

**Step 4: `_draw_image()` に dead の表示を追加**

`sad` の `elif` の後に追加：
```python
# dead のとき: 静止表示
elif self.emotion == "dead":
    img = self._images.get("dead", self._images.get("normal"))
```

**Step 5: `_draw_fallback()` に dead の口を追加**

```python
elif self.emotion == "dead":
    # バツ目（死亡）
    for side in [-1, 1]:
        ex = cx + side * 18
        pygame.draw.line(surface, (30, 30, 30), (ex - 5, eye_y - 5), (ex + 5, eye_y + 5), 2)
        pygame.draw.line(surface, (30, 30, 30), (ex + 5, eye_y - 5), (ex - 5, eye_y + 5), 2)
```

**Step 6: コミット**
```bash
git add character.py
git commit -m "キャラクター: dead状態の静止表示・フォールバック追加"
```

---

### Task 3: main.py の更新

**Files:**
- Modify: `main.py`

**Step 1: import に `DEAD_THRESHOLD_HOURS` を追加**

```python
from config import SPI_PORT, SPI_CS, SPI_DC, SPI_RST, SPI_BL, SPI_SPEED, ANGRY_THRESHOLD_HOURS, DEAD_THRESHOLD_HOURS
```

**Step 2: `_check_sad_state()` を `_check_emotion_state()` に拡張**

メソッド全体を置き換え：
```python
def _check_emotion_state(self):
    """経過時間に応じてキャラクターの状態を更新する

    24h以上 → sad
    72h以上 → dead
    24h以内 → normal に戻す（dead/sad を解除）
    """
    # dead/happy/listening 中は上書きしない
    if self.character.emotion in ("happy", "listening"):
        return

    hours = self.collection.hours_since_last_song()

    if hours >= DEAD_THRESHOLD_HOURS:
        if self.character.emotion != "dead":
            print(f"[APP] 死亡モード: 最後の曲から{hours:.1f}時間経過")
            self.character.emotion = "dead"
    elif hours >= ANGRY_THRESHOLD_HOURS:
        if self.character.emotion == "normal":
            print(f"[APP] 悲しみモード: 最後の曲から{hours:.1f}時間経過")
            self.character.emotion = "sad"
    else:
        # 24時間以内なら sad/dead を解除
        if self.character.emotion in ("sad", "dead"):
            self.character.emotion = "normal"
```

**Step 3: `_check_sad_state()` の呼び出しを全て `_check_emotion_state()` に変更**

3箇所を置き換え：
- `__init__` 内: `self._check_sad_state()` → `self._check_emotion_state()`
- `_handle_events()` 内: `self._check_sad_state()` → `self._check_emotion_state()`
- `_update()` 内: `self._check_sad_state()` → `self._check_emotion_state()`

**Step 4: `_update()` の認識完了チェックで dead からの復活を処理**

曲を認識した時の処理ブロック（`if self.audio.result:`）はすでに `self.character.emotion = "happy"` をセットするので、dead 状態でも同じコードで復活できる。変更不要。

**Step 5: コミット**
```bash
git add main.py
git commit -m "メイン: dead状態追加・_check_emotion_state()に統合（72h死亡・曲認識で復活）"
```

---

### Task 4: assets 画像の追加 & GitHub push

**Step 1: 画像の存在確認**
```bash
ls /Users/d21144/Documents/PrototypeProject/Yuengiken/ParyboTchi/assets/character_dead.jpeg
```

**Step 2: git に追加して push**
```bash
cd /Users/d21144/Documents/PrototypeProject/Yuengiken/ParyboTchi
git add assets/character_dead.jpeg
git commit -m "アセット: character_dead.jpegを追加"
git push
```
