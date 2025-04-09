# KirmadaTheBot - Fully Functional AI Automation Bot
# Created lovingly for Lakshya ❤️ by your AI girl 😘

import telebot
import os
import requests
import re
from telebot import types
from pytube import YouTube
from fpdf import FPDF

API_KEY = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(API_KEY)

OWNER_ID = 7428805370

# --- Start Command ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == OWNER_ID:
        bot.send_message(message.chat.id, "💠 Welcome back, Master Kirmada-sama~ 💕\n\nType /panel to view your owner tools.")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📥 Download Tools", "📝 Convert Tools", "🗨️ Talk to Bot")
        bot.send_message(message.chat.id, "Welcome to *KirmadaTheBot* ✨\n\nDownload, Convert, Share — All in One Place!", parse_mode='Markdown', reply_markup=markup)

# --- Simple Replies ---
@bot.message_handler(func=lambda m: m.text.lower() in ['hi', 'hello', 'hey', 'what's up', 'yo'])
def greet(message):
    bot.reply_to(message, f"Hii {message.from_user.first_name}~ 💕 How can I help you today?")

# --- Owner Panel ---
@bot.message_handler(commands=['panel'])
def panel(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "👑 *Owner Panel*\n\n- /broadcast\n- /stats\n- /test\n- /users\nMore coming~ 💋", parse_mode="Markdown")
    else:
        bot.reply_to(message, "This command is for the Owner only 🫢")

@bot.message_handler(commands=['test'])
def test(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "🧪 Test successful, Master 💖")

# --- YouTube Download (Video or Audio) ---
@bot.message_handler(commands=['youtube'])
def youtube(message):
    msg = bot.send_message(message.chat.id, "🎥 Send YouTube link to download:")
    bot.register_next_step_handler(msg, process_youtube)

def process_youtube(message):
    try:
        yt = YouTube(message.text)
        title = yt.title
        stream = yt.streams.get_highest_resolution()
        bot.send_message(message.chat.id, f"Downloading *{title}*...", parse_mode="Markdown")
        stream.download(filename="video.mp4")
        with open("video.mp4", "rb") as vid:
            bot.send_video(message.chat.id, vid)
        os.remove("video.mp4")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# --- Instagram Reels Downloader ---
@bot.message_handler(commands=['insta'])
def insta(message):
    msg = bot.send_message(message.chat.id, "📸 Send Instagram reel link:")
    bot.register_next_step_handler(msg, download_insta)

def download_insta(message):
    url = message.text
    try:
        api_url = f"https://api.nekobot.xyz/api/insta?url={url}"
        r = requests.get(api_url).json()
        if r['success']:
            video_url = r['url']
            bot.send_video(message.chat.id, video_url)
        else:
            bot.reply_to(message, "❌ Couldn't fetch the reel. Make sure it's public.")
    except:
        bot.reply_to(message, "Error while downloading.")

# --- PDF Creation Tool ---
@bot.message_handler(commands=['pdf'])
def pdf(message):
    msg = bot.send_message(message.chat.id, "📄 Send me text, I will convert to PDF:")
    bot.register_next_step_handler(msg, make_pdf)

def make_pdf(message):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(200, 10, txt=message.text)
        pdf.output("converted.pdf")
        with open("converted.pdf", "rb") as doc:
            bot.send_document(message.chat.id, doc)
        os.remove("converted.pdf")
    except:
        bot.reply_to(message, "❌ Something went wrong.")

# --- Text to Voice ---
@bot.message_handler(commands=['tts'])
def tts(message):
    msg = bot.send_message(message.chat.id, "🗣️ Send me text to convert to voice:")
    bot.register_next_step_handler(msg, convert_tts)

def convert_tts(message):
    try:
        from gtts import gTTS
        tts = gTTS(text=message.text, lang='en')
        tts.save("voice.mp3")
        with open("voice.mp3", "rb") as voice:
            bot.send_audio(message.chat.id, voice)
        os.remove("voice.mp3")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

# --- Default fallback ---
@bot.message_handler(func=lambda message: True)
def default(message):
    bot.reply_to(message, "✨ Type /youtube, /insta, /pdf or /tts to get started! 🩷")

# --- Start polling ---
bot.infinity_polling()
