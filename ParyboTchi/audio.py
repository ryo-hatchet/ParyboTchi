"""ParyboTchi - 音楽録音・認識モジュール"""

import asyncio
import threading
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from shazamio import Shazam

from config import SAMPLE_RATE, RECORD_SECONDS, RECORD_CHANNELS, TEMP_WAV_FILE


class AudioRecognizer:
    """マイクで録音し、shazamioで曲を認識するクラス"""

    def __init__(self):
        self.is_recording = False
        self.is_analyzing = False
        self._pipeline_running = False  # _run()全体をカバー（レースコンディション防止）
        self.result = None  # {"title": str, "artist": str} or None
        self.error = None
        self._thread = None

    @property
    def is_busy(self):
        return self.is_recording or self.is_analyzing or self._pipeline_running

    def start_recognition(self):
        """録音→認識を別スレッドで開始する"""
        if self.is_busy:
            return
        self.result = None
        self.error = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """録音→認識の実行（別スレッド）"""
        self._pipeline_running = True  # パイプライン全体をビジー状態に
        try:
            self._record()
            asyncio.run(self._recognize())
        except Exception as e:
            print(f"[ERROR] 録音・認識エラー: {e}")
            self.error = str(e)
            self.is_recording = False
            self.is_analyzing = False
        finally:
            self._pipeline_running = False  # 必ず解除

    def _record(self):
        """マイクから録音"""
        print(f"[REC] 録音開始 ({RECORD_SECONDS}秒)...")
        self.is_recording = True
        recording = sd.rec(
            int(RECORD_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=RECORD_CHANNELS,
        )
        sd.wait()
        wav_write(TEMP_WAV_FILE, SAMPLE_RATE, recording)
        self.is_recording = False
        print("[REC] 録音完了 → Shazam解析へ")

    async def _recognize(self):
        """shazamioで曲を認識"""
        self.is_analyzing = True
        print("[SHAZAM] 解析中...")
        shazam = Shazam(language="ja-JP")
        # recognize_song() は非推奨 → recognize() を使用
        out = await shazam.recognize(TEMP_WAV_FILE)

        track = out.get("track", {})
        if track:
            title = track.get("title", "不明")
            artist = track.get("subtitle", "不明")
            self.result = {"title": title, "artist": artist}
            print(f"[SHAZAM] 認識成功: {title} / {artist}")
        else:
            self.result = None
            self.error = "曲が見つかりませんでした"
            print("[SHAZAM] 認識失敗: 曲が見つかりませんでした")

        self.is_analyzing = False
