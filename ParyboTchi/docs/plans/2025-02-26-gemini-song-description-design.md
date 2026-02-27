# Gemini API 曲解説機能 設計書

## 概要

曲認識後にGemini APIを使って曲の解説を100文字以内で表示する機能を追加する。

## フロー

```
長押し → 録音(10秒) → Shazam認識
  → 結果表示「みつけたよ！」(既存) + バックグラウンドでGemini API呼び出し
  → 結果表示終了後、解説画面(SCREEN_DESCRIPTION)に自動遷移
  → テキスト表示（折り返し表示）
  → タップ or 自動(10秒)でメイン画面に戻る
  → Gemini失敗時はスキップしてメイン画面に戻る
```

## 新ファイル

### gemini.py - SongDescriberクラス
- `describe(title, artist)` で別スレッドからGemini APIを呼び出し
- プロンプト: 「{title} / {artist}」という曲について100文字以内で解説してください
- `is_busy`, `result`, `error` プロパティ（audio.pyと同パターン）
- google-generativeai SDKを使用

### ui_description.py - DescriptionScreenクラス
- 240x240円形ディスプレイ対応のテキスト折り返し表示
- 上部: 曲名＋アーティスト（小さめフォント）
- 中央〜下部: 解説テキスト（折り返し表示）
- 100文字以内なので基本的に1画面に収まる想定
- タイマー（10秒）で自動遷移 or タップで即遷移

## 既存ファイルの変更

### config.py
- `GEMINI_API_KEY` 追加
- `GEMINI_MODEL = "gemini-2.0-flash"` 追加
- `DESCRIPTION_DISPLAY_SECONDS = 10` 追加

### main.py
- `SCREEN_DESCRIPTION = 2` 画面状態追加
- 曲認識成功時にGemini APIをバックグラウンド呼び出し
- 結果表示終了後、Gemini結果取得済みなら解説画面に遷移
- 解説画面でのタップ/タイマー終了でメイン画面に戻る

## 設計判断
- APIキーはconfig.pyに直接記載
- 画面遷移: 自動(10秒) + タップで即座に戻れる
- エラー時: 解説画面をスキップしてメイン画面に戻る
