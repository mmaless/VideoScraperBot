from __future__ import unicode_literals
from config import telegram_token, admin_chat_id, user_chat_id, video_path, audio_path, enable_ftp, ftp_site
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from datetime import datetime
import youtube_dl
import re
import os
import logging
import time

# Enable logging
logging.basicConfig(filename='Logs/{:%Y-%m-%d}.log'.format(datetime.now()),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)

logger = logging.getLogger(__name__)

LINK_REGEX = r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"

requests = []

def start(update, context):
    update.message.reply_text(
        "Hi! this bot uses the command line utility \"youtube-dl\" https://github.com/ytdl-org/youtube-dl" +
        "to download videos or audios from YouTube.com and other video sites. \n" +
        "To download a video just send the link or use the command \\mp4 " +
        "and for audio use \\mp3 followed by the link \n" +
        "Example: \\mp4 https://www.youtube.com/watch?v=dQw4w9WgXcQ \n" +
        "Code: https://github.com/mmaless/VideoScraperBot")


def test(update, context):
    update.message.reply_text('Works!')

def request(update, context):
    if update.message.chat_id in user_chat_id:
        update.message.reply_text(
            'You already have access!')
        return
    if update.message.chat_id not in requests:
        requests.append(update.message.chat_id)
        msg = 'User: ' + update.message.chat.username + ' ID: ' + str(update.message.chat_id) + ', requested access to the bot!'
        context.bot.send_message(chat_id=admin_chat_id[0], text= msg)
        update.message.reply_text('Request submitted.')
    else:
        update.message.reply_text('Request already submitted please wait!')

def getId(update, context):
    update.message.reply_text('Your ID is: ' + str(update.message.chat_id))

def mp4list(update, context):
    if update.message.chat_id not in admin_chat_id:
        update.message.reply_text(
            'You are not authorized to perform this action!')
        return
    files = os.listdir(video_path)
    msg = ''
    for file in files:
        msg += ftp_site + 'mp4/' + file + '\n'
    update.message.reply_text(msg)


def mp3list(update, context):
    if update.message.chat_id not in admin_chat_id:
        update.message.reply_text(
            'You are not authorized to perform this action!')
        return
    files = os.listdir(audio_path)
    msg = ''
    for file in files:
        msg += ftp_site + 'mp3/' + file + '\n'
    update.message.reply_text(msg)

def mp4(update, context):
    if update.message.chat_id not in user_chat_id:
        update.message.reply_text(
            'You are not authorized to perform this action! Please submit a request by sending or clicking on this 👉 /request')
        return
    link = link_search(update.message.text)
    date = '{:%Y-%m-%d}'.format(datetime.now())
    if link:
        ydl_opts = {
            'format': 'mp4',
            'quiet': True,
            'outtmpl': video_path + date + '_%(id)s.%(ext)s',
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            video_id = info_dict.get("id", None)
            video_ext = info_dict.get("ext", None)
            ydl.download([link])
        video = date + '_{0}.{1}'.format(video_id, video_ext)
        os.utime(video_path + video, (time.time(), time.time()))
        video_size = os.path.getsize(video_path + video)
        if video_size < 50000000:
            context.bot.send_video(chat_id=update.message.chat_id, video=open(
                video_path + video, 'rb'), timeout=1000)
            if enable_ftp == 'true' :
                update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp4/' + video +'\nThe link expires after 7 days')
        else:
            if enable_ftp == 'true' :
                update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp4/' + video +'\nThe link expires after 7 days')
            else: 
                update.message.reply_text(
                    'The file size is too big and cannot be sent using Telegram')
    else:
        update.message.reply_text('That URL looks invalid')

def mp3(update, context):
    if update.message.chat_id not in user_chat_id:
        update.message.reply_text(
            'You are not authorized to perform this action! Please submit a request by sending or clicking on this 👉 /request')
        return
    link = link_search(update.message.text)
    date = '{:%Y-%m-%d}'.format(datetime.now())
    if link:
        if 'instagram' in link:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'outtmpl': audio_path + date + '_%(id)s.%(ext)s',
                'cookiefile': 'instagram.txt'
            }
        else:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'outtmpl': audio_path + date + '_%(id)s.%(ext)s'
            }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_id = info_dict.get("id", None)
            audio_ext = 'mp3'
            ydl.download([link])
        audio = date + '_{0}.{1}'.format(audio_id, audio_ext)
        os.utime(audio_path + audio, (time.time(), time.time()))
        audio_size = os.path.getsize(audio_path + audio)
        if audio_size < 50000000:
            context.bot.send_audio(chat_id=update.message.chat_id, audio=open(
                audio_path + audio, 'rb'), timeout=1000)
            if enable_ftp == 'true' :
                update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp3/' + audio +'\nThe link expires after 7 days')    
        else:
            if enable_ftp == 'true' :
                update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp3/' + audio +'\nThe link expires after 7 days')
            else: 
                update.message.reply_text(
                    'The file size is too big and cannot be sent using Telegram')
    else:
        update.message.reply_text('That URL looks invalid')


def link_search(message):
    link = re.search(LINK_REGEX, message)
    if link:
        return link.group(0)
    else:
        return ""

def error(update, context):
    update.message.reply_text('Download failed :(')
    context.bot.send_message(chat_id=admin_chat_id[0], text= 'An error occurred')
    logger.error('Update "%s" caused error "%s"', update, context.error)

def main():
    updater = Updater(telegram_token, use_context=True, request_kwargs={
                      'read_timeout': 1000, 'connect_timeout': 1000})
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('test', test))
    dp.add_handler(CommandHandler('mp4', mp4))
    dp.add_handler(CommandHandler('mp3', mp3))
    dp.add_handler(CommandHandler('mp3list', mp3list))
    dp.add_handler(CommandHandler('mp4list', mp4list))
    dp.add_handler(CommandHandler('id', getId))
    dp.add_handler(CommandHandler('request', request))
    dp.add_handler(MessageHandler(Filters.text, mp4))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
