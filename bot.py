import telebot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = 7428805370  # your admin ID

@bot.message_handler(commands=['start'])
def start(msg):
    if msg.from_user.id == OWNER_ID:
        bot.reply_to(msg, "Welcome Admin 💼")
    else:
        bot.reply_to(msg, "Hey! Welcome to KirmadaTheBot 🌀")

bot.polling()
