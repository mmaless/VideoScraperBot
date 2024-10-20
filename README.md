# Video Scraper Bot

A telegram bot that uses the command line utility [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download videos from YouTube and other video sites.

Check the [change log](https://github.com/mmaless/VideoScraperBot/blob/main/CHANGELOG.md) for the latest updates.

## Requirements

- Python 3+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
  - Install via pip:
  ```
  pip3 install python-telegram-bot --upgrade
  ```
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
  - Install via pip:
  ```
  pip3 install --upgrade yt-dlp
  ```
- ffmpeg
  - Ubuntu:
  ```
  sudo apt-get install ffmpeg
  ```
- Instagram or Twitter cookies
  - Install cookies.txt chrome extension, login to instagram and export your cookies to 'instagram.txt' file, place the file in the code directory

## Config

- authorized_ids: users that are allowed to use the bot
- video_path: location of the downloaded video files
- audio_path: location of the downloaded audio files

## Commands

- Simply just send a link to download the video
- \mp4 followed by a link to download a video
- \mp3 followed by a link to download an audio
- \test check if the bot is working
- \id get your telegram ID

## Running the bot

- Install requirements

  ```
  pip3 install -r requirements.txt
  ```

- Run the bot

  ```
  python3 scraper.py
  ```

## Running the tests

```
pytest -v
```
