# main.py
import telebot
import os
import requests
from pytube import YouTube
from fpdf import FPDF
from gtts import gTTS
from telebot import types

# Get API key from Railway environment variable
API_KEY = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(API_KEY)

# Owner/Admin configuration
OWNER_ID = 7428805370

# In-memory storage for users, referrals, and points
USERS = set()
POINTS = {}

# Temporary storage for PDF tool inputs per user
temp_pdf = {}

# --------------------------
# Utility Functions
# --------------------------

def get_affiliate_message():
    """
    Returns a standard affiliate message to be appended after downloads.
    """
    return "\n\nWant cool tools? Check out our deals: [Buy Tools Cheap](https://amzn.to/3xXWlink)"

def give_points(user_id, points=2):
    """
    Add referral points to a user.
    """
    if user_id not in POINTS:
        POINTS[user_id] = 0
    POINTS[user_id] += points

# --------------------------
# Bot Commands and Handlers
# --------------------------

# /start command: Welcome message with inline keyboard for tools and referral info.
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    USERS.add(user_id)

    # Referral logic: if /start has an extra parameter, award points to referrer
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

# Callback queries to trigger commands via inline keyboard
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'youtube':
        bot.send_message(call.from_user.id, "Send a YouTube URL to download video or audio using /youtube command.")
    elif call.data == 'insta':
        bot.send_message(call.from_user.id, "Send an Instagram Reel URL using /insta command.")
    elif call.data == 'pdf':
        bot.send_message(call.from_user.id, "Use /pdf command to start converting text/photos into a PDF. Then send /done when finished.")
    elif call.data == 'refer':
        refer(call.message)  # reuse the referral command

# /refer: Displays user's referral points and referral link.
@bot.message_handler(commands=['refer'])
def refer(message):
    uid = str(message.from_user.id)
    link = f"https://t.me/KirmadaTheBot?start={uid}"
    points = POINTS.get(message.from_user.id, 0)
    bot.reply_to(message, f"You have {points} points.\nShare this link to earn more:\n{link}")

# --------------------------
# YouTube Download
# --------------------------

# /youtube: Prompts the user to send a YouTube URL.
@bot.message_handler(commands=['youtube'])
def youtube(message):
    bot.reply_to(message, "Send a YouTube URL to download video or audio.")

# Automatic handler for messages containing a YouTube URL.
@bot.message_handler(func=lambda msg: 'youtube.com' in msg.text or 'youtu.be' in msg.text)
def yt_download(message):
    try:
        yt = YouTube(message.text)
        stream = yt.streams.get_highest_resolution()
        # Clean file name if necessary (you might want to filter out special characters)
        filename = yt.title + ".mp4"
        stream.download(filename=filename)
        with open(filename, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="Here's your video!" + get_affiliate_message(), parse_mode="Markdown")
        os.remove(filename)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# --------------------------
# Instagram Reel Downloader
# --------------------------

# /insta: Prompts the user to send an Instagram Reel URL.
@bot.message_handler(commands=['insta'])
def insta(message):
    bot.reply_to(message, "Send an Instagram Reel URL to download.")

# Dummy handler for Instagram URLs. (Many bots use third-party APIs or instruct users to use a website.)
@bot.message_handler(func=lambda msg: 'instagram.com' in msg.text)
def insta_reel(message):
    try:
        bot.reply_to(message, "Instagram downloading is limited on Telegram bots. Use this site: https://instasave.io")
    except Exception as e:
        bot.reply_to(message, "Failed to fetch reel.")

# --------------------------
# PDF Tools: Merge/Convert/Compress Text & Images
# --------------------------

# /pdf: Start collecting input for PDF creation.
@bot.message_handler(commands=['pdf'])
def pdf(message):
    bot.reply_to(message, "Send multiple text messages or photos to convert into a PDF. When you're done, send /done.")

# Collect text and photo messages for the PDF tool.
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

# /done: Process collected inputs into a PDF and send it to the user.
@bot.message_handler(commands=['done'])
def create_pdf(message):
    uid = message.from_user.id
    if uid in temp_pdf and temp_pdf[uid]:
        pdf = FPDF()
        for item in temp_pdf[uid]:
            if isinstance(item, str) and item.endswith(".jpg"):
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

# --------------------------
# Text-to-Speech (Convert Text to Voice)
# --------------------------

# /speak: Converts provided text into an audio message.
@bot.message_handler(commands=['speak'])
def tts(message):
    text = message.text.replace('/speak', '').strip()
    if not text:
        return bot.reply_to(message, "Type some text after /speak like this: /speak Hello!")
    try:
        tts = gTTS(text)
        filename = f"speech_{message.from_user.id}.mp3"
        tts.save(filename)
        with open(filename, 'rb') as f:
            bot.send_audio(message.chat.id, f)
        os.remove(filename)
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

# --------------------------
# Casual Replies for Greetings
# --------------------------

@bot.message_handler(func=lambda m: m.text.lower() in ['hi', 'hello', 'hey', "what’s up"])
def greet(message):
    bot.reply_to(message, f"Hi {message.from_user.first_name}! I’m Kirmada~ Your smart helper bot!")

# --------------------------
# Owner/Admin Panel and Commands
# --------------------------

# /panel: Displays admin tools.
@bot.message_handler(commands=['panel'])
def panel(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.reply_to(message, "👑 *Owner Panel*\n- /broadcast <msg>\n- /users\n- /test\n- /post_daily", parse_mode="Markdown")

# /users: Shows total number of users.
@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, f"Total Users: {len(USERS)}")

# /broadcast: Sends a broadcast message to all users.
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.replace('/broadcast', '').strip()
    for user in USERS:
        try:
            bot.send_message(user, f"[Broadcast]\n{text}")
        except Exception as e:
            pass

# /test: Owner test command.
@bot.message_handler(commands=['test'])
def test(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "Admin mode is active. All functions working fine!")

# /post_daily: Automatically posts a daily message to a specified group/channel.
@bot.message_handler(commands=['post_daily'])
def post_daily(message):
    if message.from_user.id != OWNER_ID:
        return bot.reply_to(message, "You’re not allowed!")
    text = "Here's your daily tip from Kirmada~ ✨\nDid you know you can convert text to voice using /speak?"
    group_id = -100123456789  # Replace with your actual group/channel ID
    bot.send_message(group_id, text)

# --------------------------
# Start the Bot
# --------------------------
bot.infinity_polling()
