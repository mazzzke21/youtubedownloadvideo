import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from PIL import Image, ImageTk
from .downloader import Downloader
from .utils import validate_youtube_url
from .config import DEFAULT_QUALITY, QUALITIES, FORMATS, AUDIO_ONLY_FORMATS, DOWNLOADS_DIR
import io

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('YouTube Video Downloader')
        self.geometry('700x500')
        self.resizable(False, False)
        ctk.set_appearance_mode('system')
        ctk.set_default_color_theme('blue')

        # Always use downloads in project root
        self.download_dir = DOWNLOADS_DIR
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # --- Top: Link and Info ---
        self.url_frame = ctk.CTkFrame(self)
        self.url_frame.pack(fill='x', pady=(20, 0), padx=20)
        self.url_label = ctk.CTkLabel(self.url_frame, text='YouTube link:')
        self.url_label.pack(side='left', padx=(0, 10))
        # Используем обычный Entry для вставки
        self.url_entry = tk.Entry(self.url_frame, width=50, font=("Arial", 13))
        self.url_entry.pack(side='left', padx=(0, 10), ipady=3)
        self.info_btn = ctk.CTkButton(self.url_frame, text='Get Info', width=80, command=self.get_info)
        self.info_btn.pack(side='left')

        # --- Контекстное меню для вставки ---
        self.url_menu = tk.Menu(self, tearoff=0)
        self.url_menu.add_command(label="Вставить", command=self.paste_url)
        self.url_entry.bind("<Button-3>", self.show_url_menu)
        self.url_entry.bind("<Control-v>", self.paste_url_event)

        # --- Video Info ---
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill='x', pady=(10, 0), padx=20)
        self.title_label = ctk.CTkLabel(self.info_frame, text='', font=('', 14, 'bold'))
        self.title_label.pack(anchor='w')
        self.meta_label = ctk.CTkLabel(self.info_frame, text='', font=('', 10))
        self.meta_label.pack(anchor='w')
        self.thumb_label = ctk.CTkLabel(self.info_frame, text='')
        self.thumb_label.pack(anchor='w', pady=(5, 0))

        # --- Download Options ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(fill='x', pady=(15, 0), padx=20)
        # Format
        self.format_label = ctk.CTkLabel(self.options_frame, text='Format:')
        self.format_label.grid(row=0, column=0, sticky='w', padx=(0, 5), pady=5)
        self.format_combobox = ctk.CTkComboBox(self.options_frame, values=FORMATS, width=100)
        self.format_combobox.set('mp4')
        self.format_combobox.grid(row=0, column=1, sticky='w', pady=5)
        # Quality
        self.quality_label = ctk.CTkLabel(self.options_frame, text='Quality:')
        self.quality_label.grid(row=0, column=2, sticky='w', padx=(20, 5), pady=5)
        self.quality_combobox = ctk.CTkComboBox(self.options_frame, values=QUALITIES, width=100)
        self.quality_combobox.set(DEFAULT_QUALITY)
        self.quality_combobox.grid(row=0, column=3, sticky='w', pady=5)
        # Only audio
        self.audio_var = tk.BooleanVar()
        self.audio_check = ctk.CTkCheckBox(self.options_frame, text='Audio only', variable=self.audio_var, command=self.toggle_audio)
        self.audio_check.grid(row=1, column=0, sticky='w', pady=5)
        # Subtitles
        self.subs_var = tk.BooleanVar()
        self.subs_check = ctk.CTkCheckBox(self.options_frame, text='Download subtitles', variable=self.subs_var)
        self.subs_check.grid(row=1, column=1, sticky='w', pady=5)
        # Playlist
        self.playlist_var = tk.BooleanVar()
        self.playlist_check = ctk.CTkCheckBox(self.options_frame, text='Download playlist', variable=self.playlist_var)
        self.playlist_check.grid(row=1, column=2, sticky='w', pady=5)
        # Custom options
        self.custom_label = ctk.CTkLabel(self.options_frame, text='Custom yt-dlp options:')
        self.custom_label.grid(row=2, column=0, sticky='w', pady=5)
        self.custom_entry = ctk.CTkEntry(self.options_frame, width=350)
        self.custom_entry.grid(row=2, column=1, columnspan=3, sticky='w', pady=5)
        # Download folder (readonly)
        self.dir_label = ctk.CTkLabel(self.options_frame, text=f'Download folder: {self.download_dir}', font=('', 10))
        self.dir_label.grid(row=3, column=0, columnspan=4, sticky='w', pady=(10, 0))

        # --- Download Button ---
        self.download_btn = ctk.CTkButton(self, text='Download', command=self.start_download, width=200)
        self.download_btn.pack(pady=15)

        # --- Progress and Status ---
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0)
        self.progress.pack(pady=5)
        self.status_label = ctk.CTkLabel(self, text='')
        self.status_label.pack(pady=5)
        self.speed_label = ctk.CTkLabel(self, text='')
        self.speed_label.pack()

        self.downloader = Downloader(self.update_progress, self.on_finish)
        self.video_info = None
        self.thumbnail_img = None

    def show_url_menu(self, event):
        try:
            self.url_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.url_menu.grab_release()

    def paste_url(self):
        try:
            self.url_entry.insert(tk.INSERT, self.clipboard_get())
        except tk.TclError:
            pass

    def paste_url_event(self, event):
        self.paste_url()
        return "break"

    def toggle_audio(self):
        if self.audio_var.get():
            self.format_combobox.set('mp3')
            self.quality_combobox.configure(state='disabled')
        else:
            self.quality_combobox.configure(state='normal')
            self.format_combobox.set('mp4')

    def get_info(self):
        url = self.url_entry.get().strip()
        if not validate_youtube_url(url):
            messagebox.showerror('Error', 'Please enter a valid YouTube link!')
            return
        self.status_label.configure(text='Getting video info...')
        self.update()
        info = self.downloader.get_video_info(url)
        if info is None:
            self.status_label.configure(text='Failed to get video info')
            return
        self.video_info = info
        self.title_label.configure(text=info.get('title', ''))
        meta = f"Duration: {info.get('duration_string', '')} | Author: {info.get('uploader', '')}"
        self.meta_label.configure(text=meta)
        # Thumbnail
        thumb_url = info.get('thumbnail')
        if thumb_url:
            try:
                from urllib.request import urlopen
                img_bytes = urlopen(thumb_url).read()
                img = Image.open(io.BytesIO(img_bytes)).resize((120, 68))
                self.thumbnail_img = ImageTk.PhotoImage(img)
                self.thumb_label.configure(image=self.thumbnail_img, text='')
            except Exception:
                self.thumb_label.configure(image=None, text='[No thumbnail]')
        else:
            self.thumb_label.configure(image=None, text='[No thumbnail]')
        self.status_label.configure(text='')

    def start_download(self):
        url = self.url_entry.get().strip()
        if not validate_youtube_url(url):
            messagebox.showerror('Error', 'Please enter a valid YouTube link!')
            return
        if self.downloader.downloading:
            return
        self.progress.set(0)
        self.status_label.configure(text='Preparing...')
        self.speed_label.configure(text='')
        self.download_btn.configure(state='disabled')
        quality = self.quality_combobox.get() or DEFAULT_QUALITY
        fmt = self.format_combobox.get()
        audio_only = self.audio_var.get()
        subs = self.subs_var.get()
        playlist = self.playlist_var.get()
        custom_opts = self.custom_entry.get().strip()
        self.downloader.download(
            url, quality, self.download_dir, fmt=fmt, audio_only=audio_only, subs=subs, playlist=playlist, custom_opts=custom_opts
        )

    def update_progress(self, percent, speed, eta):
        self.progress.set(percent/100)
        self.status_label.configure(text=f'Downloading: {percent}%')
        if speed:
            speed_str = f'{speed/1024/1024:.2f} MB/s'
        else:
            speed_str = ''
        self.speed_label.configure(text=f'Speed: {speed_str}  ETA: {eta} sec')

    def on_finish(self, success, error=None):
        self.download_btn.configure(state='normal')
        if success:
            self.status_label.configure(text='Download completed!')
            self.speed_label.configure(text='')
        else:
            self.status_label.configure(text='Error!')
            messagebox.showerror('Error', f'Failed to download video:\n{error}')

def run_app():
    app = App()
    app.mainloop() 