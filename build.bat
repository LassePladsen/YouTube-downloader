$echo off
pyinstaller --onefile --noconsole --icon "E:\Lasse\Dokumenter\Dev\Python prosjekter\YouTube downloader\data\icon.ico" --add-data "E:\Lasse\Dokumenter\Dev\Python prosjekter\YouTube downloader\data;data" -n "YouTube Downloader" main.py

