# bot.py
import telebot
import os

API_KEY = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(API_KEY)

OWNER_ID = 7428805370  # your admin user ID

# START COMMAND
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "💠 Welcome back, Master Kirmada-sama~ 💕\n\nType /panel to view your owner tools.")
    else:
        bot.reply_to(message, "Welcome to KirmadaTheBot 🔥\nUse /youtube, /insta, /pdf and more!")

# OWNER PANEL
@bot.message_handler(commands=['panel'])
def panel(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "👑 *Owner Panel*\n\n- /broadcast\n- /stats\n- /test\n- /users\nMore coming~ 💋", parse_mode="Markdown")
    else:
        bot.reply_to(message, "This command is for the Owner only 🫢")

# TEST COMMAND FOR OWNER
@bot.message_handler(commands=['test'])
def test(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "🔬 Test successful! You're seeing this as the Admin.")
    else:
        bot.reply_to(message, "You're a normal user~ 😋")

# Normal Commands
@bot.message_handler(commands=['youtube'])
def youtube(message):
    bot.reply_to(message, "📥 Send me a YouTube link to download.")

@bot.message_handler(commands=['insta'])
def insta(message):
    bot.reply_to(message, "🎞️ Send me an Instagram reel link to save.")

@bot.message_handler(commands=['pdf'])
def pdf(message):
    bot.reply_to(message, "📄 Send a PDF to begin editing or converting.")

bot.infinity_polling()
