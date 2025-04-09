import telebot
import os
from telebot import types
import json

# Set API Key securely
API_KEY = os.environ.get("BOT_TOKEN")
if not API_KEY:
    # Fallback for testing - remove in production
    API_KEY = "YOUR_BOT_TOKEN_HERE"  # Replace with your token for testing only

bot = telebot.TeleBot(API_KEY)

# Constants
OWNER_ID = 7428805370  # Your owner ID
USERS = set()
POINTS = {}
PREMIUM_USERS = set()
USAGE_LIMITS = {}
REFERRALS = {}

# Database functions (simple file-based)
def load_data():
    global USERS, POINTS, PREMIUM_USERS, REFERRALS, USAGE_LIMITS
    try:
        if os.path.exists('database.json'):
            with open('database.json', 'r') as f:
                data = json.load(f)
                USERS = set(data.get('users', []))
                POINTS = {int(k): v for k, v in data.get('points', {}).items()}
                PREMIUM_USERS = set(data.get('premium', []))
                REFERRALS = {int(k): v for k, v in data.get('referrals', {}).items()}
                USAGE_LIMITS = {int(k): v for k, v in data.get('usage_limits', {}).items()}
    except Exception as e:
        print(f"Error loading data: {e}")

def save_data():
    try:
        data = {
            'users': list(USERS),
            'points': POINTS,
            'premium': list(PREMIUM_USERS),
            'referrals': REFERRALS,
            'usage_limits': USAGE_LIMITS
        }
        with open('database.json', 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving data: {e}")

# Load data at startup
load_data()

# Main menu markup
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📹 YouTube Download", callback_data='youtube'),
        types.InlineKeyboardButton("📱 Instagram Reel", callback_data='insta')
    )
    markup.add(
        types.InlineKeyboardButton("📄 PDF Tools", callback_data='pdf'),
        types.InlineKeyboardButton("🎁 Refer & Earn", callback_data='refer')
    )
    markup.add(
        types.InlineKeyboardButton("💰 My Points", callback_data='points'),
        types.InlineKeyboardButton("✨ Premium", callback_data='premium')
    )
    return markup

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    USERS.add(user_id)
    save_data()
    
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "💠 Welcome back, Master Kirmada-sama~ 💕\n\nType /panel to view your owner tools.")
    else:
        welcome_text = """
✨ *Welcome to KirmadaTheBot* ✨

Your all-in-one solution for:
• YouTube & Instagram downloads
• PDF creation tools
• Text-to-Speech conversion
• Image effects and more!

Earn rewards by using the bot and referring friends!
"""
        bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

# Owner Panel
@bot.message_handler(commands=['panel'])
def panel(message):
    if message.from_user.id == OWNER_ID:
        stats = f"👥 Total Users: {len(USERS)}\n💎 Premium Users: {len(PREMIUM_USERS)}"
        bot.reply_to(message, f"👑 *Owner Panel*\n\n{stats}\n\n- /broadcast\n- /stats\n- /test\n- /users\nMore coming~ 💋", parse_mode="Markdown")
    else:
        bot.reply_to(message, "This command is for the Owner only 🫢")

# Test Command for Owner
@bot.message_handler(commands=['test'])
def test(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "🔬 Test successful! You're seeing this as the Admin.")
    else:
        bot.reply_to(message, "You're a normal user~ 😋")

# Stats Command for Owner
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == OWNER_ID:
        stats_text = f"""
📊 *Bot Statistics*

👥 Users: {len(USERS)}
💎 Premium Users: {len(PREMIUM_USERS)}
🔄 Total Referrals: {sum(len(refs) for refs in REFERRALS.values())}
        """
        bot.reply_to(message, stats_text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "This command is for the Owner only 🫢")

# Callback Handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == 'youtube':
        bot.send_message(user_id, "🎬 Send a YouTube URL to download video or audio")
    
    elif call.data == 'insta':
        bot.send_message(user_id, "📱 Send Instagram Reel or Post URL")
    
    elif call.data == 'pdf':
        bot.send_message(user_id, "📄 Send text starting with /pdf_text to convert to PDF")
    
    elif call.data == 'refer':
        link = f"https://t.me/KirmadaTheBot?start={user_id}"
        points = POINTS.get(user_id, 0)
        referrals = len(REFERRALS.get(user_id, []))
        
        bot.send_message(user_id, f"🔗 *Your Referral Link*\n{link}\n\n📊 Stats:\n- Points: {points}\n- Referrals: {referrals}\n\nEarn 5 points for each new user!", parse_mode="Markdown")
    
    elif call.data == 'points':
        points = POINTS.get(user_id, 0)
        bot.send_message(user_id, f"💰 *Your Points*: {points}\n\nEarn points by:\n- Daily login: +1 point\n- Referrals: +5 points per user\n- Using features: +2 points", parse_mode="Markdown")
    
    elif call.data == 'premium':
        premium_status = "✅ ACTIVE" if user_id in PREMIUM_USERS else "❌ INACTIVE"
        benefits = """
✨ *Premium Benefits*:
• No daily usage limits
• No ads/affiliate links
• 5x daily bonus points
• Priority processing
• Exclusive features
        """
        bot.send_message(user_id, f"💎 *Premium Status*: {premium_status}\n{benefits}\n\nCurrent Points: {POINTS.get(user_id, 0)}", parse_mode="Markdown")
    
    # Clear the callback query
    bot.answer_callback_query(call.id)

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

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📚 *Available Commands*:

• /start - Start the bot
• /youtube - Download YouTube videos
• /insta - Save Instagram reels
• /pdf - PDF tools
• /refer - Refer friends
• /points - Check your points
• /premium - Premium features
• /help - Show this message

Send me a YouTube or Instagram link to get started!
"""
    bot.reply_to(message, help_text, parse_mode="Markdown")

# Handle simple text messages
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.lower()
    
    # Handle YouTube links
    if 'youtube.com' in text or 'youtu.be' in text:
        bot.reply_to(message, "I see you sent a YouTube link! This feature is coming soon.")
        return
        
    # Handle Instagram links
    if 'instagram.com' in text:
        bot.reply_to(message, "I see you sent an Instagram link! This feature is coming soon.")
        return
    
    # For other random messages
    if text in ['hi', 'hello', 'hey']:
        bot.reply_to(message, f"Hey {message.from_user.first_name}! How can I help you today? Try /help for commands.")
    else:
        bot.reply_to(message, "I'm not sure what you mean. Try /help for available commands.")

# Start the bot
if __name__ == "__main__":
    print("Bot starting...")
    try:
        print(f"Bot username: {bot.get_me().username}")
        print("Bot is running - press Ctrl+C to stop")
        bot.infinity_polling(timeout=20, long_polling_timeout=5)
    except Exception as e:
        print(f"Bot error: {e}")
