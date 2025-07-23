import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, 'downloads')

DEFAULT_QUALITY = '1080p'
QUALITIES = ['2160p','1440p','1080p','720p','480p','360p','240p','144p']

FORMATS = [
    'mp4', 'webm', 'mkv', 'mp3', 'm4a', 'bestaudio', 'bestvideo', 'best',
]

AUDIO_ONLY_FORMATS = ['mp3', 'm4a', 'bestaudio']

# Можно расширять по мере добавления новых опций 