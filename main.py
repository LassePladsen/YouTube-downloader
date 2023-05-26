import tkinter as tk
from tkinter import ttk
from pytube import YouTube,exceptions,Stream
from typing import Union
import asyncio
import threading

DOWNLOAD_PATH = r"G:\Users\Joachim\Downloads"
WINDOW_WIDTH = 220
WINDOW_HEIGHT = 180

async def async_download_message():
    result_label.configure(text="Downloading...")


def download():
    url = url_entry.get()
    if not url:
        result_label.configure(text="Invalid URL.")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def download_task():
        await async_download_message()
        format_type = format_var.get()
        resolution = resolution_var.get()
        stream, outstring = get_stream(url, format_type, resolution)
        result_label.configure(text=outstring)

    def start_download():
        loop.run_until_complete(download_task())
        loop.close()

    threading.Thread(target=start_download).start()

def get_stream(url: str, format_type: str, resolution: str) -> tuple[Union[Stream, None], str]:
    outstring = ""
    try:
        video = YouTube(url)
    except exceptions.RegexMatchError:
        outstring = f"No video found."
        return None, outstring

    stream = None
    try:
        if format_type == "mp4":
            stream = get_mp4_stream(video,resolution)
        elif format_type == "mp3":
            stream = video.streams.get_audio_only()
        else:
            result_label.configure(text="Invalid format.")
    except exceptions.AgeRestrictedError:
        outstring = "Download failed, video is age restricted."
        return None, outstring

    if stream is None:   # no stream gotten
        outstring = f"No stream found in {resolution}."
    else:
        stream.download(DOWNLOAD_PATH, filename=stream.default_filename.replace("mp4", format_type))
        if format_type == "mp4":
            outstring = rf"Video downloaded in {stream.resolution}."
        elif format_type == "mp3":
            outstring = rf"Audio downloaded with bitrate: {stream.bitrate}."

    return stream, outstring

def get_mp4_stream(video: YouTube, quality: str) -> Stream:
    if quality == "Max (w/ audio)":
        return video.streams.get_highest_resolution()
    else:
        return video.streams.get_by_resolution(quality)

def on_format_select(*args):
    selected_format = format_var.get()
    if selected_format == "mp4":
        resolution_combo.configure(state="readonly")
        resolution_var.set("Max (w/ audio)")
    else:
        resolution_combo.configure(state="disabled")
        resolution_var.set("")   # Clear the resolution selection

root = tk.Tk()
root.title("YouTube Downloader")

# Calculate the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the x and y coordinates for the window to be centered
x = int((screen_width / 2) - (WINDOW_WIDTH / 2))
y = int((screen_height / 2) - (WINDOW_HEIGHT / 2))

# Set the window's position
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

# URL input
url_label = ttk.Label(root, text="URL:")
url_label.pack()

url_entry = ttk.Entry(root, width=35)
url_entry.pack()

# Format selection
format_label = ttk.Label(root, text="Format:")
format_label.pack()

format_var = tk.StringVar()
format_var.set("mp4")
format_combo = ttk.Combobox(root, textvariable=format_var, values=["mp4", "mp3"],state="readonly")
format_combo.pack()

format_var.trace("w", on_format_select)

# Resolution selection
resolution_label = ttk.Label(root, text="Resolution:")
resolution_label.pack()

resolution_var = tk.StringVar()
resolution_var.set("Max (w/ audio)")
resolution_combo = ttk.Combobox(root, textvariable=resolution_var,
                                values=["Max (w/ audio)","1080p (muted)", "720p", "480p", "360p"])
resolution_combo.pack()

# Download button
download_button = ttk.Button(root, text="Download", command=download)
download_button.pack(pady=5)

# Result label
result_label = ttk.Label(root, text="",wraplength=WINDOW_WIDTH)
result_label.pack()

# Initialize resolution combo box state
resolution_combo.configure(state="readonly")

root.mainloop()
