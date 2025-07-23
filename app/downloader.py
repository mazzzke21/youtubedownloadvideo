import threading
import yt_dlp
import os

def build_ydl_opts(quality, outdir, fmt=None, audio_only=False, subs=False, playlist=False, custom_opts=None):
    # Формируем опции yt-dlp на основе параметров
    height = ''.join(filter(str.isdigit, quality))
    format_str = None
    if audio_only:
        format_str = 'bestaudio/best'
    elif fmt and fmt in ['mp3', 'm4a', 'bestaudio']:
        format_str = 'bestaudio/best'
    elif fmt and fmt in ['mp4', 'webm', 'mkv', 'bestvideo', 'best']:
        format_str = f'bestvideo[height={height}][ext={fmt}]+bestaudio[ext=m4a]/best[height={height}][ext={fmt}]/best'
    else:
        format_str = f'bestvideo[height={height}]+bestaudio/best'
    opts = {
        'format': format_str,
        'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
        'merge_output_format': fmt if fmt else 'mp4',
        'progress_hooks': [],
        'noplaylist': not playlist,
        'quiet': True,
        'no_warnings': True,
    }
    if subs:
        opts['writesubtitles'] = True
        opts['subtitleslangs'] = ['en', 'ru', 'original']
        opts['writeautomaticsub'] = True
    if audio_only or (fmt and fmt in ['mp3', 'm4a']):
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': fmt if fmt in ['mp3', 'm4a'] else 'mp3',
            'preferredquality': '192',
        }]
    if custom_opts:
        # ВНИМАНИЕ: это строка, пользователь может сломать загрузку
        # Можно парсить и добавлять в opts, но пока просто игнорируем
        pass
    return opts

class Downloader:
    def __init__(self, progress_callback, finish_callback):
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.downloading = False

    def get_video_info(self, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                # duration_string для удобства
                if 'duration' in info:
                    mins, secs = divmod(info['duration'], 60)
                    info['duration_string'] = f"{mins}:{secs:02d}"
                return info
        except Exception:
            return None

    def download(self, url, quality, outdir, fmt=None, audio_only=False, subs=False, playlist=False, custom_opts=None):
        def run():
            self.downloading = True
            ydl_opts = build_ydl_opts(quality, outdir, fmt, audio_only, subs, playlist, custom_opts)
            ydl_opts['progress_hooks'] = [self.progress_hook]
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.finish_callback(success=True)
            except Exception as e:
                self.finish_callback(success=False, error=str(e))
            self.downloading = False
        threading.Thread(target=run, daemon=True).start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            percent = int(downloaded / total * 100) if total else 0
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            self.progress_callback(percent, speed, eta) 