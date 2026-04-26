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
