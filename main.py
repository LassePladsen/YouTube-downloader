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


WINDOW_WIDTH = 281
WINDOW_HEIGHT = 190
CONFIG_JSON_PATH = get_absolute_path("data/config.json")
FOLDER_IMAGE_PATH = get_absolute_path("data/folder.png")
FOLDER_IMAGE_SIZE = 35, 35
DOWNLOAD_FOLDER_TITLE = "Select a Download Directory"


async def async_download_message() -> None:
    result_label.configure(text="Downloading...")


def download() -> None:
    url = url_entry.get()
    if not url:
        result_label.configure(text="Invalid URL.")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # All this async code is to display "downloading..." status message as the download is processing.
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


def get_stream(url: str, format_type: str, resolution: str) -> tuple[Stream | None, str]:
    outstring = ""
    try:
        video = YouTube(url)
    except exceptions.RegexMatchError:
        outstring = f"No video found."
        return None, outstring

    stream = None
    try:
        if format_type == "mp4":
            stream = get_mp4_stream(video, resolution)
        elif format_type == "mp3":
            stream = video.streams.get_audio_only()
        else:
            result_label.configure(text="Invalid format.")
    except exceptions.AgeRestrictedError:
        outstring = "Download failed, video is age restricted."
        return None, outstring
    except exceptions.RegexMatchError:
        outstring = "RegexMatchError getting the video stream."
        return None, outstring

    if stream is None:  # no stream gotten
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


root = tk.Tk()
root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
root.title("YouTube Downloader")

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
download_button.pack(pady=5)

# Result label
result_label = ttk.Label(root, text="", wraplength=WINDOW_WIDTH, style="Red.TLabel")
result_label.pack()

# Initialize resolution combo box state
resolution_combo.configure(state="readonly")

# Change download folder button
folder_photo_image = tk.PhotoImage(file=FOLDER_IMAGE_PATH).subsample(FOLDER_IMAGE_SIZE[0], FOLDER_IMAGE_SIZE[1])
folder_button = ttk.Button(root, image=folder_photo_image, command=change_download_folder)
folder_button.place(relx=0.98, rely=0.98, anchor="se")  # place at the right bottom of the window

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
