from __future__ import unicode_literals
from config import telegram_token, admin_chat_id, user_chat_id, video_path, audio_path, enable_ftp, ftp_site
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters
from datetime import datetime
from yt_dlp import YoutubeDL
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


async def start(update, context):
    await update.message.reply_text(
        "Hi! this bot uses the command line utility \"yt-dlp\" https://github.com/yt-dlp/yt-dlp " +
        "to download videos or audios from YouTube.com and other video sites. \n" +
        "To download a video just send the link or use the command \\mp4 " +
        "and for audio use \\mp3 followed by the link \n" +
        "Example: \\mp4 https://www.youtube.com/watch?v=dQw4w9WgXcQ \n" +
        "Code: https://github.com/mmaless/VideoScraperBot")


async def test(update, context):
    await update.message.reply_text('Works!')


async def request(update, context):
    if update.message.chat_id in user_chat_id:
        await update.message.reply_text(
            'You already have access!')
        return
    if update.message.chat_id not in requests:
        requests.append(update.message.chat_id)
        msg = 'User: ' + update.message.chat.username + ' ID: ' + \
            str(update.message.chat_id) + ', requested access to the bot!'
        await context.bot.send_message(chat_id=admin_chat_id[0], text=msg)
        await update.message.reply_text('Request submitted.')
    else:
        await update.message.reply_text('Request already submitted please wait!')


async def getId(update, context):
    await update.message.reply_text('Your ID is: ' + str(update.message.chat_id))


async def mp4list(update, context):
    if update.message.chat_id not in admin_chat_id:
        await update.message.reply_text(
            'You are not authorized to perform this action!')
        return
    files = os.listdir(video_path)
    msg = ''
    for file in files:
        msg += ftp_site + 'mp4/' + file + '\n'
    if (msg == ''):
        await update.message.reply_text('No files found')
    else:
        await update.message.reply_text(msg)


async def mp3list(update, context):
    if update.message.chat_id not in admin_chat_id:
        await update.message.reply_text(
            'You are not authorized to perform this action!')
        return
    files = os.listdir(audio_path)
    msg = ''
    for file in files:
        msg += ftp_site + 'mp3/' + file + '\n'
    if (msg == ''):
        await update.message.reply_text('No files found')
    else:
        await update.message.reply_text(msg)


async def mp4(update, context):
    if update.message.chat_id not in user_chat_id:
        await update.message.reply_text(
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
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            video_id = info_dict.get("id", None)
            video_ext = info_dict.get("ext", None)
            ydl.download([link])
        video = date + '_{0}.{1}'.format(video_id, video_ext)
        os.utime(video_path + video, (time.time(), time.time()))
        video_size = os.path.getsize(video_path + video)
        if video_size < 50000000:
            await context.bot.send_video(chat_id=update.message.chat_id, video=open(
                video_path + video, 'rb'))
            if enable_ftp == 'true':
                await update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp4/' + video + '\nThe link expires after 7 days')
        else:
            if enable_ftp == 'true':
                await update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp4/' + video + '\nThe link expires after 7 days')
            else:
                await update.message.reply_text(
                    'The file size is too big and cannot be sent using Telegram')
    else:
        await update.message.reply_text('That URL looks invalid')


async def mp3(update, context):
    if update.message.chat_id not in user_chat_id:
        await update.message.reply_text(
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
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_id = info_dict.get("id", None)
            audio_ext = 'mp3'
            ydl.download([link])
        audio = date + '_{0}.{1}'.format(audio_id, audio_ext)
        os.utime(audio_path + audio, (time.time(), time.time()))
        audio_size = os.path.getsize(audio_path + audio)
        if audio_size < 50000000:
            await context.bot.send_audio(chat_id=update.message.chat_id, audio=open(
                audio_path + audio, 'rb'))
            if enable_ftp == 'true':
                await update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp3/' + audio + '\nThe link expires after 7 days')
        else:
            if enable_ftp == 'true':
                await update.message.reply_text(
                    'The file can be downloaded using the below link:\n' + ftp_site + 'mp3/' + audio + '\nThe link expires after 7 days')
            else:
                await update.message.reply_text(
                    'The file size is too big and cannot be sent using Telegram')
    else:
        await update.message.reply_text('That URL looks invalid')


def link_search(message):
    link = re.search(LINK_REGEX, message)
    if link:
        return link.group(0)
    else:
        return ""


async def error(update, context):
    await update.message.reply_text('Download failed :(')
    await context.bot.send_message(
        chat_id=admin_chat_id[0], text='An error occurred')
    logger.error('Update "%s" caused error "%s"', update, context.error)


def main():
    app = ApplicationBuilder().token(telegram_token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('test', test))
    app.add_handler(CommandHandler('mp4', mp4))
    app.add_handler(CommandHandler('mp3', mp3))
    app.add_handler(CommandHandler('mp3list', mp3list))
    app.add_handler(CommandHandler('mp4list', mp4list))
    app.add_handler(CommandHandler('id', getId))
    app.add_handler(CommandHandler('request', request))
    app.add_handler(MessageHandler(filters.TEXT, mp4))
    app.add_error_handler(error)
    app.run_polling()


if __name__ == '__main__':
    main()
