import asyncio
import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog

from pytube import YouTube, exceptions, Stream


def get_absolute_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


WINDOW_WIDTH = 285
WINDOW_HEIGHT = 205
CONFIG_JSON_PATH = get_absolute_path("data/config.json")
FOLDER_IMAGE_PATH = get_absolute_path("data/folder.png")
ICON_IMAGE_PATH = get_absolute_path("data/icon.ico")
FOLDER_IMAGE_SUBSAMPLE = 35, 35
DOWNLOAD_FOLDER_TITLE = "Select a Download Directory"


async def set_result_label_async_message(message: str) -> None:
    result_label.configure(text=message)


def download() -> None:
    url = url_entry.get()
    if not url:
        result_label.configure(text="Invalid URL")
        return

    progress_bar.pack()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # All this async code is to display "downloading..." status message as the download is processing.
    async def download_task():
        await set_result_label_async_message("Getting video...")
        format_type = format_var.get()
        resolution = resolution_var.get()
        download_video_stream(url, format_type, resolution)

    def start_download():
        loop.run_until_complete(download_task())
        loop.close()
        progress_bar.pack_forget()

    threading.Thread(target=start_download).start()


def download_video_stream(url: str, format_type: str, resolution: str) -> None:
    match format_type:
        case "mp4":
            file_type = "video"
        case "mp3":
            file_type = "audio"
        case _:
            result_label.configure(text="Invalid format")
            return
    result_label.configure(text=f"Getting {file_type}...")
    try:
        video = YouTube(url, on_progress_callback=on_progress, on_complete_callback=on_complete)
    except exceptions.RegexMatchError:
        result_label.configure(text=f"No video found")
        return
    except exceptions:
        result_label.configure(text=f"Error getting video")
        return
    stream = None
    try:
        if format_type == "mp4":
            stream = get_mp4_stream(video, resolution)
        elif format_type == "mp3":
            stream = video.streams.get_audio_only()
        else:
            result_label.configure(text="Invalid format")
    except exceptions.AgeRestrictedError:
        result_label.configure(text="Download failed, video is age restricted")
        return
    except exceptions:
        result_label.configure(text="Unknown error getting the video stream")
        return
    if stream is None:  # no stream gotten
        result_label.configure(text=f"No stream found in {resolution}")
    else:
        stream.download(DOWNLOAD_PATH, filename=stream.default_filename.replace("mp4", format_type))


def get_mp4_stream(video: YouTube, quality: str) -> Stream:
    if quality == "Max (w/ audio)":
        return video.streams.get_highest_resolution()
    else:
        return video.streams.get_by_resolution(quality)


def on_format_select(*args) -> None:
    selected_format = format_var.get()
    if selected_format == "mp4":
        resolution_combo.configure(state="readonly")
        resolution_var.set("Max (w/ audio)")
    else:
        resolution_combo.configure(state="disabled")
        resolution_var.set("")  # Clear the resolution selection


def file_exists(filename: str) -> bool:
    """Checks if a file exists."""
    try:
        with open(filename, "r"):
            pass
        return True
    except FileNotFoundError:
        return False


def get_json_data(key: str, file: str = CONFIG_JSON_PATH) -> str:
    """Extracts string value from given datakey from a given .json filename. Defaults to discord_data.json"""
    if not file_exists(file):
        change_download_folder()
    with open(file, "r") as infile:
        data = json.load(infile)
    return data[key]


def set_json_data(key: str, value: str, file: str = CONFIG_JSON_PATH) -> None:
    """Sets a key and value in a given .json filename. Defaults to discord_data.json"""
    with open(file, "r") as infile:
        data = json.load(infile)
    data[key] = value
    with open(file, "w") as outfile:
        json.dump(data, outfile, indent=3)


def change_download_folder() -> None:
    """Changes the download folder."""
    filepath = filedialog.askdirectory(title=DOWNLOAD_FOLDER_TITLE)
    if filepath:
        set_json_data("download_path", filepath)


def on_progress(stream, chunk, bytes_remaining) -> None:
    """Function on download progress callback event in get_stream().
    It updates result label and the progress bar."""
    progress_bar.pack()
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = int(round(bytes_downloaded / total_size * 100, 0))
    result_label.configure(text=f"Downloading {stream.type}... {percent}%")
    result_label.update()
    progress_bar["value"] = float(percent)
    progress_bar.update()


def on_complete(stream, file_handle) -> None:
    """Function on download complete callback event in get_stream().
    It updates result label and hides the progress bar."""
    max_chars = 80
    # max_chars = 68
    title = stream.title
    match stream.type:
        case "video":
            text = f"Downloaded '{title}.mp4' in {stream.resolution}!"
            if len(text) > max_chars:  # video title too long
                chars = len(text) - max_chars - 4
                text = f"Downloaded '{title[:chars]}... .mp4' in {stream.resolution}!"
        case "audio":
            text = f"Downloaded '{title}.mp3' with bitrate {stream.bitrate}!"
            if len(text) > max_chars:  # video title too long
                chars = len(text) - max_chars - 4
                text = f"Downloaded '{title[:chars]}... .mp3' with bitrate {stream.bitrate}!"
        case _:
            text = f"Downloaded '{title}'!"
            if len(text) > max_chars:  # video title too long
                text = text[:max_chars] + "..."

    result_label.configure(text=text)
    progress_bar.pack_forget()


root = tk.Tk()
root.resizable(False, False)
root.title("YouTube Downloader")
root.iconbitmap(ICON_IMAGE_PATH)

# Check if download path is set, if not, ask for it
if file_exists(CONFIG_JSON_PATH):
    with open(CONFIG_JSON_PATH, "r") as f:
        DOWNLOAD_PATH = get_json_data("download_path")
else:
    DOWNLOAD_PATH = filedialog.askdirectory(title=DOWNLOAD_FOLDER_TITLE)
    with open(CONFIG_JSON_PATH, "w") as f:
        json.dump({"download_path": DOWNLOAD_PATH}, f)

# Styling
style = ttk.Style().configure(
        "Red.TLabel", foreground="red", font=("Arial", 10, "bold")
)

# Set the window's position in the middle of the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = int((screen_width / 2) - (WINDOW_WIDTH / 2))
y = int((screen_height / 2) - (WINDOW_HEIGHT / 2))
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
format_combo = ttk.Combobox(root, textvariable=format_var, values=["mp4", "mp3"], state="readonly")
format_combo.pack()

format_var.trace("w", on_format_select)

# Resolution selection
resolution_label = ttk.Label(root, text="Resolution:")
resolution_label.pack()

resolution_var = tk.StringVar()
resolution_var.set("Max (w/ audio)")
resolution_combo = ttk.Combobox(root, textvariable=resolution_var,
                                values=["Max (w/ audio)", "1080p (muted)", "720p", "480p", "360p"])
resolution_combo.pack()

# Download button
download_button = ttk.Button(root, text="Download", command=download)
download_button.pack(pady=3)

# Result label
result_label = ttk.Label(root, text="", wraplength=WINDOW_WIDTH, style="Red.TLabel")
result_label.pack()

# Download progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=WINDOW_WIDTH * 0.8)
# dont pack yet

# Initialize resolution combo box state
resolution_combo.configure(state="readonly")

# Change download folder button
folder_photo_image = tk.PhotoImage(file=FOLDER_IMAGE_PATH).subsample(FOLDER_IMAGE_SUBSAMPLE[0],
                                                                     FOLDER_IMAGE_SUBSAMPLE[1])
folder_button = ttk.Button(root, image=folder_photo_image, command=change_download_folder)
folder_button.place(relx=0.995, rely=0.005, anchor="ne")
if __name__ == "__main__":
    root.mainloop()

"""note: When getting pytube.exceptions.RegetMatchError when getting streams from a YouTube object, temp. workaround is 
on 'https://github.com/pytube/pytube/issues/1678' from 'mrmechanik':
The first regex in the function_patterns (cipher.py -> get_throttling_function_name -> function_patterns) does not have a capture group for the method name so I added one:

r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)'

Tested with 3 different videos.
This is probably only a quick fix.

Final code segment:

    function_patterns = [
        # https://github.com/ytdl-org/youtube-dl/issues/29326#issuecomment-865985377
        # https://github.com/yt-dlp/yt-dlp/commit/48416bc4a8f1d5ff07d5977659cb8ece7640dcd8
        # var Bpa = [iha];
        # ...
        # a.C && (b = a.get("n")) && (b = Bpa[0](b), a.set("n", b),
        # Bpa.length || iha("")) }};
        # In the above case, `iha` is the relevant function name
        r'a\.[a-zA-Z]\s*&&\s*\([a-z]\s*=\s*a\.get\("n"\)\)\s*&&.*?\|\|\s*([a-z]+)',
        r'\([a-z]\s*=\s*([a-zA-Z0-9$]+)(\[\d+\])?\([a-z]\)',
    ]
"""
