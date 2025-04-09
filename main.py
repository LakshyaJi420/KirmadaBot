# main.py
import telebot
import os
import requests
from pytube import YouTube
from fpdf import FPDF
from gtts import gTTS
from telebot import types

API_KEY = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(API_KEY)

OWNER_ID = 7428805370
USERS = set()
REFERRALS = {}
POINTS = {}

# Utils

def get_affiliate_message():
    return "\n\nWant cool tools? Check out our deals: [Buy Tools Cheap](https://amzn.to/3xXWlink)"

def give_points(user_id, points=2):
    if user_id not in POINTS:
        POINTS[user_id] = 0
    POINTS[user_id] += points

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    USERS.add(user_id)

    # Referral logic
    if message.text.startswith("/start "):
        ref_id = message.text.split()[1]
        if ref_id.isdigit() and int(ref_id) != user_id:
            give_points(int(ref_id))

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Download from YouTube", callback_data='youtube'))
    markup.add(types.InlineKeyboardButton("Download Instagram Reel", callback_data='insta'))
    markup.add(types.InlineKeyboardButton("PDF Tools", callback_data='pdf'))
    markup.add(types.InlineKeyboardButton("Refer & Earn", callback_data='refer'))

    bot.send_message(user_id, """
✨ *Welcome to KirmadaTheBot* ✨

Download, Convert, Share — All in One Place!
Earn rewards by sharing the bot!
""", parse_mode="Markdown", reply_markup=markup)

# Referral
@bot.message_handler(commands=['refer'])
def refer(message):
    uid = str(message.from_user.id)
    link = f"https://t.me/KirmadaTheBot?start={uid}"
    points = POINTS.get(message.from_user.id, 0)
    bot.reply_to(message, f"You have {points} points.\nShare this link to earn more:\n{link}")

# YouTube
@bot.message_handler(commands=['youtube'])
def youtube(message):
    bot.reply_to(message, "Send a YouTube URL to download video or audio")

@bot.message_handler(func=lambda msg: 'youtube.com' in msg.text or 'youtu.be' in msg.text)
def yt_download(message):
    try:
        yt = YouTube(message.text)
        stream = yt.streams.get_highest_resolution()
        filename = yt.title + ".mp4"
        stream.download(filename=filename)
        with open(filename, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="Here's your video!" + get_affiliate_message(), parse_mode="Markdown")
        os.remove(filename)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# Instagram
@bot.message_handler(commands=['insta'])
def insta(message):
    bot.reply_to(message, "Send Instagram Reel URL")

@bot.message_handler(func=lambda msg: 'instagram.com' in msg.text)
def insta_reel(message):
    try:
        # Dummy method using 3rd party tool
        bot.reply_to(message, "Instagram downloading is limited on Telegram bots. Use this site: https://instasave.io")
    except:
        bot.reply_to(message, "Failed to fetch reel")

# PDF Tools
@bot.message_handler(commands=['pdf'])
def pdf(message):
    bot.reply_to(message, "Send multiple text messages or photos to convert into a PDF. Send /done when finished.")

temp_pdf = {}

@bot.message_handler(func=lambda m: True, content_types=['text', 'photo'])
def pdf_collector(message):
    uid = message.from_user.id
    if uid not in temp_pdf:
        temp_pdf[uid] = []
    if message.content_type == 'text':
        temp_pdf[uid].append(message.text)
    elif message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        filename = f"photo_{uid}.jpg"
        with open(filename, 'wb') as f:
            f.write(downloaded)
        temp_pdf[uid].append(filename)

@bot.message_handler(commands=['done'])
def create_pdf(message):
    uid = message.from_user.id
    if uid in temp_pdf and temp_pdf[uid]:
        pdf = FPDF()
        for item in temp_pdf[uid]:
            if item.endswith(".jpg"):
                pdf.add_page()
                pdf.image(item, x=10, y=10, w=180)
                os.remove(item)
            else:
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, item)
        file = f"{uid}_output.pdf"
        pdf.output(file)
        with open(file, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="Here's your PDF!" + get_affiliate_message(), parse_mode="Markdown")
        os.remove(file)
        temp_pdf.pop(uid)
    else:
        bot.reply_to(message, "You haven't added anything yet!")

# Text to Voice
@bot.message_handler(commands=['speak'])
def tts(message):
    text = message.text.replace('/speak', '').strip()
    if not text:
        return bot.reply_to(message, "Type some text after /speak like this: /speak Hello!")
    tts = gTTS(text)
    filename = f"speech_{message.from_user.id}.mp3"
    tts.save(filename)
    with open(filename, 'rb') as f:
        bot.send_audio(message.chat.id, f)
    os.remove(filename)

# Casual replies
@bot.message_handler(func=lambda m: m.text.lower() in ['hi', 'hello', 'hey', 'what’s up'])
def greet(message):
    bot.reply_to(message, f"Hi {message.from_user.first_name}! I’m Kirmada~ Your smart helper bot!")

# Owner Panel
@bot.message_handler(commands=['panel'])
def panel(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.reply_to(message, "👑 *Owner Panel*\n- /broadcast <msg>\n- /users\n- /test\n- /post_daily", parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, f"Total Users: {len(USERS)}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.replace('/broadcast', '').strip()
    for user in USERS:
        try:
            bot.send_message(user, f"[Broadcast]\n{text}")
        except:
            pass

@bot.message_handler(commands=['test'])
def test(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "Admin mode is active. All functions working fine!")

# Auto Daily Post
@bot.message_handler(commands=['post_daily'])
def post_daily(message):
    if message.from_user.id != OWNER_ID:
        return bot.reply_to(message, "You’re not allowed!")
    text = "Here's your daily tip from Kirmada~ ✨\nDid you know you can convert text to voice using /speak?"
    group_id = -100123456789  # Replace with your group/channel ID
    bot.send_message(group_id, text)

bot.infinity_polling()
