from __future__ import unicode_literals
from config import telegram_token, admin_chat_id, video_path, audio_path, ftp_site
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from datetime import datetime
import youtube_dl
import re
import os
import logging

# Enable logging
logging.basicConfig(filename='Logs/{:%Y-%m-%d}.log'.format(datetime.now()),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)

LINK_REGEX = r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"


def start(bot, update):
    update.message.reply_text(
        "Hi! this bot uses the command line utility \"youtube-dl\" " +
        "to download videos or audios from YouTube.com and other video sites. \n" +
        "To download a video simply just send the link or use the command \\mp4 " +
        "and for audio use \\mp3 followed by the link \n" +
        "Example: \\mp4 https://www.youtube.com/watch?v=dQw4w9WgXcQ'")


def test(bot, update):
    update.message.reply_text('Works!')


def mp4(bot, update):
    if update.message.chat_id not in admin_chat_id:
        error(bot, str(update.message.chat_id), 'failed attempt to download')
        update.message.reply_text(
            'You are not authorized to perform this action!')
        return
    link = link_searh(update.message.text)
    if link:
        ydl_opts = {
            'format': 'mp4',
            'quiet': True,
            'outtmpl': video_path + '%(id)s.%(ext)s',
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            video_id = info_dict.get("id", None)
            video_ext = info_dict.get("ext", None)
            ydl.download([link])
        video = '{0}.{1}'.format(video_id, video_ext)
        video_size = os.path.getsize(video_path + video)
        if video_size < 50000000:
            bot.send_video(chat_id=update.message.chat_id, video=open(
                video_path + video, 'rb'), timeout=1000)
        else:
            update.message.reply_text(
                'The file can be downloaded using the below link:\n' + ftp_site + 'mp4/' + video)
    else:
        update.message.reply_text('That URL looks invalid')


def mp3(bot, update):
    if update.message.chat_id not in admin_chat_id:
        return
    link = link_searh(update.message.text)
    if link:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'outtmpl': audio_path + '%(id)s.mp3'
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_id = info_dict.get("id", None)
            audio_ext = 'mp3'
            ydl.download([link])
        audio = '{0}.{1}'.format(audio_id, audio_ext)
        audio_size = os.path.getsize(audio_path + audio)
        if audio_size < 50000000:
            bot.send_audio(chat_id=update.message.chat_id, audio=open(
                audio_path + audio, 'rb'), timeout=1000)
        else:
            update.message.reply_text(
                'The file can be downloaded using the below link:\n' + ftp_site + 'mp3/' + audio)
    else:
        update.message.reply_text('That URL looks invalid')


def link_searh(message):
    link = re.search(LINK_REGEX, message)
    if link:
        return link.group(0)
    else:
        return ""


def error(bot, update, error):
    logger.error('Update "%s" caused error "%s"', update, error)


def main():
    updater = Updater(token=telegram_token, request_kwargs={
                      'read_timeout': 1000, 'connect_timeout': 1000})
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('test', test))
    dp.add_handler(CommandHandler('mp4', mp4))
    dp.add_handler(CommandHandler('mp3', mp3))
    dp.add_handler(MessageHandler(Filters.text, mp4))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
