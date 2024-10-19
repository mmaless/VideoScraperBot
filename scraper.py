import re
import logging
from functools import wraps
from config import telegram_token, authorized_ids, video_path, audio_path
from version import __version__
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, CallbackContext
from datetime import datetime
from yt_dlp import YoutubeDL
from typing import Callable, Awaitable, Dict
from pathlib import Path
import requests

MAX_FILESIZE_MB = 50
LINK_REGEX = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"


def create_folders_if_not_exist(folder_paths):
    """Checks if the specified folders exist and creates them if they do not."""
    for folder in folder_paths:
        path = Path(folder)
        path.mkdir(parents=True, exist_ok=True)


create_folders_if_not_exist(['logs', video_path, audio_path])

logging.basicConfig(filename=f'logs/{datetime.now():%Y-%m-%d}.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)


def url_search(message: str) -> str:
    """Extracts the first URL found in a message using regex."""
    link = re.search(LINK_REGEX, message)
    return link.group(0) if link else ""


async def start(update: Update, _: CallbackContext) -> None:
    """Sends a welcome message explaining how to use the bot."""
    await update.message.reply_text(
        "\n".join(
            ["Hi!",
             "This bot uses the command line utility [yt-dlp](https://github.com/yt-dlp/yt-dlp)",
             "to download videos or audios from YouTube.com and other video sites.",
             "To download a video just send the link or use the command \\mp4 and for audio use \\mp3 followed by the link",
             "Example: `\\mp4 https://www.youtube.com/watch?v=dQw4w9WgXcQ`",
             "This is an open-source [project](https://github.com/mmaless/VideoScraperBot)",
             f"You are using version: {__version__}"]),
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


def get_opts(video_url: str, opts_type: str) -> Dict[str, object]:
    """Generates download options for video or audio."""
    date = f'{datetime.now():%Y-%m-%d}'
    opts = {
        'format': 'best' if opts_type == 'video' else 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'outtmpl': f"{video_path if opts_type == 'video' else audio_path}{date}_%(id)s.%(ext)s",
    }
    if opts_type == 'audio':
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    if 'instagram.com' in video_url:
        opts['cookiefile'] = 'instagram.txt'
    elif 'twitter.com' in video_url or 'x.com' in video_url:
        opts['cookiefile'] = 'twitter.txt'
    return opts


def get_video_info(video_url: str, ydl_opts: Dict[str, object]) -> float:
    """Retrieves video file size, without downloading."""
    if video_url.endswith(('.mp4', '.mp3')):
        response = requests.head(video_url)
        if 'Content-Length' in response.headers:
            file_size = int(response.headers['Content-Length'])
            file_size_mb = file_size / (1024 * 1024)
            return file_size_mb
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        filesize = info.get('filesize') or info.get('filesize_approx')
        return filesize / (1024 ** 2) if filesize else 0


def authorize(func: Callable[[Update, CallbackContext], Awaitable[None]]) -> Callable[[Update, CallbackContext], Awaitable[None]]:
    """Decorator to authorize users."""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs) -> None:
        user_id = update.effective_user.id
        if user_id not in authorized_ids:
            await update.message.reply_text("You are not authorized to use this bot.")
            return
        await func(update, context, *args, **kwargs)
    return wrapper


def validate_url(func: Callable[[Update, CallbackContext], Awaitable[None]]) -> Callable[[Update, CallbackContext], Awaitable[None]]:
    """Decorator to validate URL from message."""
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext, *args, **kwargs) -> None:
        video_url = url_search(update.message.text)
        if not video_url:
            await update.message.reply_text('That URL looks invalid.')
            return
        await func(update, context, *args, **kwargs)
    return wrapper


@authorize
async def test(update: Update, _: CallbackContext) -> None:
    """Test command to check bot authorization."""
    await update.message.reply_text('Works!')


@authorize
async def getId(update: Update, _: CallbackContext) -> None:
    """Returns the user's chat ID."""
    await update.message.reply_text(f'Your ID is: {update.effective_user.id}')


@authorize
@validate_url
async def mp4(update: Update, context: CallbackContext, force: bool = False) -> None:
    """Downloads video from a provided URL."""
    video_url = url_search(update.message.text)
    ydl_opts = get_opts(video_url, 'video')
    if not force:
        video_size = get_video_info(video_url, ydl_opts)
        if video_size > MAX_FILESIZE_MB:
            await update.message.reply_text(
                f'The file size ({video_size:.2f} MB) is too big and '
                f'cannot be sent using Telegram.'
            )
            return
    date = f'{datetime.now():%Y-%m-%d}'
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        video_id = info_dict.get("id")
        video_ext = info_dict.get("ext")
        ydl.download([video_url])
    video = f"{date}_{video_id}.{video_ext}"
    if force:
        await update.message.reply_text(f'You chose to force download a video. It will not be sent via Telegram.')
        return
    await context.bot.send_video(chat_id=update.effective_user.id, video=open(f"{video_path}{video}", 'rb'))


@authorize
async def force(update: Update, context: CallbackContext) -> None:
    """Forces downloading a video even if the file size exceeds the limit."""
    await mp4(update, context, force=True)


@authorize
@validate_url
async def mp3(update: Update, context: CallbackContext) -> None:
    """Downloads audio from a provided URL."""
    video_url = url_search(update.message.text)
    ydl_opts = get_opts(video_url, 'audio')

    audio_size = get_video_info(video_url, ydl_opts)
    if audio_size > MAX_FILESIZE_MB:
        await update.message.reply_text(
            f'The file size ({audio_size:.2f} MB) is too big and '
            f'cannot be sent using Telegram.'
        )
        return
    date = f'{datetime.now():%Y-%m-%d}'
    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        audio_id = info_dict.get("id")
        ydl.download([video_url])
    audio = f"{date}_{audio_id}.mp3"
    await context.bot.send_audio(chat_id=update.effective_user.id, audio=open(f"{audio_path}{audio}", 'rb'))


async def error(update: Update, context: CallbackContext) -> None:
    """Handles errors during command execution."""
    await update.message.reply_text('An error occurred! You have to check the logs.')
    logger.error('Update "%s" caused error "%s"', update, context.error)


def main() -> None:
    """Starts the bot and sets up handlers."""
    app = ApplicationBuilder().token(telegram_token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('test', test))
    app.add_handler(CommandHandler('mp4', mp4))
    app.add_handler(CommandHandler('mp3', mp3))
    app.add_handler(CommandHandler('id', getId))
    app.add_handler(CommandHandler('force', force))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mp4))
    app.add_error_handler(error)
    app.run_polling()


if __name__ == '__main__':
    main()
