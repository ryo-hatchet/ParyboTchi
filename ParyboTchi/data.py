"""ParyboTchi - データ管理モジュール（曲コレクションの永続化）"""

import json
import os
from datetime import datetime, timezone

from config import DATA_FILE, GROWTH_STAGES


class SongCollection:
    """集めた曲のコレクションを管理するクラス"""

    def __init__(self):
        self.songs = []
        self.load()

    def load(self):
        """JSONファイルからコレクションを読み込む"""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.songs = json.load(f)

    def save(self):
        """コレクションをJSONファイルに保存する"""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.songs, f, ensure_ascii=False, indent=2)

    def add_song(self, title: str, artist: str) -> bool:
        """曲を追加する。重複の場合はFalseを返す"""
        for song in self.songs:
            if song["title"] == title and song["artist"] == artist:
                return False

        self.songs.append({
            "title": title,
            "artist": artist,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self.save()
        return True

    @property
    def count(self):
        return len(self.songs)

    def get_growth_stage(self):
        """現在の成長段階を返す"""
        stage = GROWTH_STAGES[0]
        for s in GROWTH_STAGES:
            if self.count >= s["min_songs"]:
                stage = s
        return stage

    def get_next_stage(self):
        """次の成長段階と、あと何曲必要かを返す"""
        current = self.get_growth_stage()
        for i, s in enumerate(GROWTH_STAGES):
            if s["name"] == current["name"] and i + 1 < len(GROWTH_STAGES):
                next_stage = GROWTH_STAGES[i + 1]
                remaining = next_stage["min_songs"] - self.count
                return next_stage, remaining
        return None, 0

    def hours_since_last_song(self) -> float:
        """最後に曲を追加してからの経過時間（時間）を返す。
        曲が一度もない場合は inf を返す。
        """
        if not self.songs:
            return float("inf")
        last_date_str = self.songs[-1]["date"]  # "YYYY-MM-DD HH:MM" 形式
        try:
            last_dt = datetime.strptime(last_date_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return float("inf")
        now = datetime.now()
        diff = now - last_dt
        return diff.total_seconds() / 3600
