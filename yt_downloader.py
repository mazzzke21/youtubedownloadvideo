import tkinter as tk
from tkinter import ttk, messagebox
import threading
import yt_dlp
import re
import os
from tkinter import filedialog
from tkinter import StringVar
from tkinter.ttk import Combobox

class MyLogger:
    def __init__(self, progress_callback):
        self.progress_callback = progress_callback
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(msg)
    def info(self, msg):
        pass
    def progress_hook(self, d):
        self.progress_callback(d)

def download_video(url, progress_callback, on_finish):
    ydl_opts = {
        'format': 'bestvideo[height=1080][ext=mp4][vcodec^=h264]+bestaudio[ext=m4a]/best[height=1080][ext=mp4][vcodec^=h264]/best',
        'outtmpl': '%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'logger': MyLogger(progress_callback),
        'progress_hooks': [progress_callback],
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        on_finish(success=True)
    except Exception as e:
        on_finish(success=False, error=str(e))

# GUI
class App:
    def __init__(self, root):
        self.root = root
        self.root.title('YouTube 1080p MP4 Downloader')
        self.root.geometry('500x270')
        self.root.resizable(False, False)

        self.download_dir = os.getcwd()

        self.menu_bar = tk.Menu(root)
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label='Choose download folder', command=self.choose_download_dir)
        self.menu_bar.add_cascade(label='Settings', menu=self.settings_menu)
        root.config(menu=self.menu_bar)

        self.url_label = tk.Label(root, text='YouTube link:')
        self.url_label.pack(pady=(20, 0))
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)

        # Quality selection
        self.quality_label = tk.Label(root, text='Quality:')
        self.quality_label.pack()
        self.quality_var = StringVar()
        self.quality_combobox = Combobox(root, textvariable=self.quality_var, state='readonly', width=10)
        self.quality_combobox['values'] = ('2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p')
        self.quality_combobox.current(2)  # 1080p default
        self.quality_combobox.pack(pady=2)

        self.download_btn = tk.Button(root, text='Download', command=self.start_download)
        self.download_btn.pack(pady=10)

        self.progress = ttk.Progressbar(root, orient='horizontal', length=350, mode='determinate')
        self.progress.pack(pady=5)
        self.progress['value'] = 0

        self.status_label = tk.Label(root, text='')
        self.status_label.pack(pady=5)

        self.speed_label = tk.Label(root, text='')
        self.speed_label.pack()

        self.dir_label = tk.Label(root, text=f'Download folder: {self.download_dir}', font=(None, 8))
        self.dir_label.pack(pady=(2, 0))

        self.downloading = False

    def choose_download_dir(self):
        folder = filedialog.askdirectory(initialdir=self.download_dir, title='Choose download folder')
        if folder:
            self.download_dir = folder
            self.dir_label.config(text=f'Download folder: {self.download_dir}')

    def start_download(self):
        url = self.url_entry.get().strip()
        if not re.match(r'^https?://(www\.)?youtube\.com|youtu\.be', url):
            messagebox.showerror('Error', 'Please enter a valid YouTube link!')
            return
        if self.downloading:
            return
        self.progress['value'] = 0
        self.status_label.config(text='Preparing...')
        self.speed_label.config(text='')
        self.download_btn.config(state='disabled')
        self.downloading = True
        quality = self.quality_var.get()
        if not quality:
            quality = '1080p'
        threading.Thread(target=self._download_thread, args=(url, quality), daemon=True).start()

    def _download_thread(self, url, quality):
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                percent = int(downloaded / total * 100) if total else 0
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                self.progress['value'] = percent
                self.status_label.config(text=f'Downloading: {percent}%')
                if speed:
                    speed_str = f'{speed/1024/1024:.2f} MB/s'
                else:
                    speed_str = ''
                self.speed_label.config(text=f'Speed: {speed_str}  ETA: {eta} sec')
            elif d['status'] == 'finished':
                self.progress['value'] = 100
                self.status_label.config(text='Done!')
                self.speed_label.config(text='')

        def on_finish(success, error=None):
            self.download_btn.config(state='normal')
            self.downloading = False
            if success:
                self.status_label.config(text='Download completed!')
            else:
                self.status_label.config(text='Error!')
                messagebox.showerror('Error', f'Failed to download video:\n{error}')

        # Pass download path and quality
        def download_video_with_dir_and_quality(url, progress_callback, on_finish, outdir, quality):
            # Convert quality to height
            height = ''.join(filter(str.isdigit, quality))
            ydl_opts = {
                'format': f'bestvideo[height={height}][ext=mp4][vcodec^=h264]+bestaudio[ext=m4a]/best[height={height}][ext=mp4][vcodec^=h264]/best',
                'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'logger': MyLogger(progress_callback),
                'progress_hooks': [progress_callback],
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                on_finish(success=True)
            except Exception as e:
                on_finish(success=False, error=str(e))

        download_video_with_dir_and_quality(url, progress_hook, on_finish, self.download_dir, quality)

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == '__main__':
    main() 