"""
Shazam-test.py
Raspberry Pi Zero 2 の microUSB 接続マイクで音声を録音し、
曲名とアーティスト名を特定するテストスクリプト。
"""

import asyncio
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import os
from shazamio import Shazam

# --- 設定 ---
SAMPLE_RATE = 44100   # サンプルレート (Hz)
DURATION = 10         # 録音秒数
CHANNELS = 1          # モノラル


def list_audio_devices():
    """利用可能なオーディオデバイスを表示する"""
    print("=== 利用可能なオーディオデバイス ===")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  [{i}] {device['name']} (入力チャンネル: {device['max_input_channels']})")
    print()


def record_audio(duration=DURATION, sample_rate=SAMPLE_RATE, device=None):
    """
    マイクから音声を録音する

    Args:
        duration: 録音秒数
        sample_rate: サンプルレート
        device: 使用するデバイスのインデックス (None でデフォルト)

    Returns:
        録音データ (numpy array)
    """
    print(f"録音開始... ({duration}秒間)")
    audio_data = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=CHANNELS,
        dtype=np.int16,
        device=device
    )
    sd.wait()
    print("録音完了")
    return audio_data


async def recognize_song(audio_data, sample_rate=SAMPLE_RATE):
    """
    録音した音声データをShazamで認識する

    Args:
        audio_data: 録音データ (numpy array)
        sample_rate: サンプルレート

    Returns:
        認識結果の辞書、または None
    """
    # 一時ファイルに WAV 形式で保存
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        wav.write(tmp_path, sample_rate, audio_data)
        print("Shazamで認識中...")

        shazam = Shazam()
        result = await shazam.recognize(tmp_path)
        return result

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def print_result(result):
    """認識結果を表示する"""
    print("\n=== 認識結果 ===")

    if not result:
        print("結果なし")
        return

    track = result.get("track")
    if not track:
        print("曲が認識できませんでした")
        return

    title = track.get("title", "不明")
    subtitle = track.get("subtitle", "不明")  # アーティスト名

    print(f"曲名:     {title}")
    print(f"アーティスト: {subtitle}")

    # 追加情報があれば表示
    genres = track.get("genres", {}).get("primary", None)
    if genres:
        print(f"ジャンル:   {genres}")


async def main():
    print("=== Shazam マイク認識テスト ===\n")

    # デバイス一覧を表示
    list_audio_devices()

    # デバイス番号を指定したい場合は以下のコメントを外す
    # DEVICE_INDEX = 0
    # audio_data = record_audio(device=DEVICE_INDEX)

    # デフォルトデバイスで録音
    try:
        audio_data = record_audio()
    except Exception as e:
        print(f"録音エラー: {e}")
        print("ヒント: デバイス一覧から正しいインデックスを確認し、DEVICE_INDEX を設定してください")
        return

    # Shazam で認識
    try:
        result = await recognize_song(audio_data)
        print_result(result)
    except Exception as e:
        print(f"認識エラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
