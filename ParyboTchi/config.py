"""ParyboTchi - 設定ファイル"""

import os
import platform

# --- 環境判定 ---
IS_RASPBERRY_PI = platform.system() == "Linux" and (
    platform.machine().startswith("aarch64") or platform.machine().startswith("arm")
)

# --- 画面設定 ---
SCREEN_SIZE = 240
SCREEN_CENTER = SCREEN_SIZE // 2
FPS = 30

# --- 色定義 ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
BG_COLOR = (0, 0, 0)  # 完全な黒
ACCENT_COLOR = (100, 200, 255)
HAPPY_COLOR = (255, 220, 100)
NOTE_COLOR = (255, 150, 200)
LISTENING_COLOR = (150, 255, 150)
TEXT_COLOR = WHITE
TITLE_COLOR = ACCENT_COLOR
ARTIST_COLOR = LIGHT_GRAY

# --- 録音設定 ---
SAMPLE_RATE = 44100
RECORD_SECONDS = 7
RECORD_CHANNELS = 1
TEMP_WAV_FILE = os.path.join(os.path.dirname(__file__), "temp_rec.wav")

# --- データ保存 ---
DATA_FILE = os.path.join(os.path.dirname(__file__), "collection.json")

# --- キャラクター画像 (assets/ フォルダに配置) ---
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
CHARACTER_IMAGES = {
    "normal": os.path.join(ASSETS_DIR, "character_normal.jpeg"),
    "blink": os.path.join(ASSETS_DIR, "character_blink.jpeg"),
    "listening": os.path.join(ASSETS_DIR, "character_listening.jpeg"),
    # happy がなければ listening → normal の順でフォールバック
    "happy": os.path.join(ASSETS_DIR, "character_happy.jpeg"),
}

# --- GPIO設定 (Raspberry Pi) ---
BUTTON_A_PIN = 22  # メインボタン (録音/決定) ※GPIO17はTP_RSTと競合するため変更
BUTTON_B_PIN = 27  # サブボタン (画面切り替え/スクロール)

# --- キャラクター成長段階 ---
GROWTH_STAGES = [
    {"name": "たまご", "min_songs": 0},
    {"name": "ベビー", "min_songs": 3},
    {"name": "こども", "min_songs": 10},
    {"name": "ヤング", "min_songs": 25},
    {"name": "おとな", "min_songs": 50},
    {"name": "マスター", "min_songs": 100},
]

# --- ステージ称号 ---
STAGE_TITLES = {
    "たまご":  "初心者DJ",
    "ベビー":  "ほどほどなDJ",
    "こども":  "中級DJ",
    "ヤング":  "音楽マニア",
    "おとな":  "ディグの神様",
    "マスター": "異常なオタク",
}

# --- SPI設定 (GC9A01ディスプレイ) ---
SPI_PORT = 0
SPI_CS = 0
SPI_DC = 25
SPI_RST = 24
SPI_BL = 18
SPI_SPEED = 40000000
