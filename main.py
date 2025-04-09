import telebot
import os
import requests
from pytube import YouTube
from fpdf import FPDF
from gtts import gTTS
from telebot import types
import time
import re
import random
from io import BytesIO
from PIL import Image, ImageFilter
import json
from datetime import datetime, timedelta

# Set API Key securely
API_KEY = os.environ.get("BOT_TOKEN", "7930757231:AAFHc49RHS_BGy0DIDSPK1YXlXXkUCLB6nI")
bot = telebot.TeleBot(API_KEY)

from dotenv import load_dotenv
load_dotenv()  # Add this near the top of your file

# Constants
OWNER_ID = 7428805370  # Your owner ID
USERS = set()
REFERRALS = {}
POINTS = {}
DAILY_BONUS = {}
TEMP_STORAGE = {}
PREMIUM_USERS = set()
USAGE_LIMITS = {}
USER_ACTIVITY = {}
PREMIUM_COST = 100  # points to become premium

# Affiliate links - you can add your own links here
AFFILIATE_LINKS = {
    "amazon": "https://amzn.to/3xXWlink",
    "aliexpress": "https://s.click.aliexpress.com/yourlink",
    "hostinger": "https://hostinger.com/?REFERRALCODE=yourcode",
    "digitalocean": "https://m.do.co/c/yourcode",
    "books": "https://amzn.to/booklink",
    "tools": "https://amzn.to/toolslink",
    "gadgets": "https://amzn.to/gadgetslink",
    "vpn": "https://nordvpn.com/refer/yourcode",
    "courses": "https://udemy.com/affiliate/yourcode"
}

# Monetization products
PRODUCTS = {
    "premium_month": {"name": "Premium Membership (1 Month)", "price": 5, "points": 200},
    "premium_year": {"name": "Premium Membership (1 Year)", "price": 40, "points": 2000},
    "unlimited_downloads": {"name": "Unlimited Downloads (1 Week)", "price": 3, "points": 100},
    "no_ads": {"name": "Remove Ads (1 Month)", "price": 2, "points": 80}
}

# Database functions (simple file-based for Railway.com)
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

# Utils
def get_affiliate_message():
    """Return a random affiliate message based on what function was used"""
    categories = list(AFFILIATE_LINKS.keys())
    category = random.choice(categories)
    link = AFFILIATE_LINKS[category]
    
    messages = [
        f"\n\n👉 Love using this bot? Support us by checking out great deals on {category}: [Check it out]({link})",
        f"\n\n🔥 Exclusive {category} offers for our bot users: [Limited Time Deals]({link})",
        f"\n\n💡 Get amazing {category} at discounted prices: [Special Offer]({link})",
        f"\n\n🎁 While you wait, check out these {category} deals: [Click Here]({link})"
    ]
    return random.choice(messages)

def get_premium_message():
    """Return a message to promote premium features"""
    return "\n\n✨ *Upgrade to Premium* to remove ads and get unlimited usage! Type /premium for details."

def check_user_limits(user_id):
    """Check if user has reached their daily limits"""
    if user_id in PREMIUM_USERS:
        return True  # Premium users have no limits
        
    today = time.strftime("%Y-%m-%d")
    
    if user_id not in USAGE_LIMITS:
        USAGE_LIMITS[user_id] = {"date": today, "count": 0}
    
    # Reset counter if it's a new day
    if USAGE_LIMITS[user_id]["date"] != today:
        USAGE_LIMITS[user_id] = {"date": today, "count": 0}
    
    # Check if user has reached daily limit (10 for free users)
    if USAGE_LIMITS[user_id]["count"] >= 10:
        return False
        
    # Increment usage count
    USAGE_LIMITS[user_id]["count"] += 1
    save_data()
    return True

def give_points(user_id, points=2):
    """Add points to user account"""
    if user_id not in POINTS:
        POINTS[user_id] = 0
    POINTS[user_id] += points
    save_data()
    return POINTS[user_id]

def check_daily_bonus(user_id):
    """Give daily bonus points to user"""
    today = time.strftime("%Y-%m-%d")
    if user_id not in DAILY_BONUS or DAILY_BONUS[user_id] != today:
        DAILY_BONUS[user_id] = today
        points = 5 if user_id in PREMIUM_USERS else 1  # Premium users get 5x bonus
        give_points(user_id, points)
        return points
    return 0

def track_activity(user_id, action):
    """Track user activity for analytics"""
    if user_id not in USER_ACTIVITY:
        USER_ACTIVITY[user_id] = []
    USER_ACTIVITY[user_id].append({
        "action": action,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# Main menu markup
def get_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📹 YouTube Download", callback_data='youtube'),
        types.InlineKeyboardButton("📱 Instagram Reel", callback_data='insta')
    )
    markup.add(
        types.InlineKeyboardButton("📄 PDF Tools", callback_data='pdf'),
        types.InlineKeyboardButton("🔊 Text-to-Speech", callback_data='tts')
    )
    markup.add(
        types.InlineKeyboardButton("🖼️ Image Effects", callback_data='image'),
        types.InlineKeyboardButton("🎁 Refer & Earn", callback_data='refer')
    )
    markup.add(
        types.InlineKeyboardButton("💰 My Points", callback_data='points'),
        types.InlineKeyboardButton("✨ Premium", callback_data='premium')
    )
    
    # Add occasional promotional button
    if random.randint(1, 5) == 1:  # 20% chance to show promo
        promo_buttons = [
            types.InlineKeyboardButton("🛍️ Shop Deals", url=AFFILIATE_LINKS['amazon']),
            types.InlineKeyboardButton("📚 Learn More", url=AFFILIATE_LINKS['courses']),
            types.InlineKeyboardButton("🔒 Get VPN", url=AFFILIATE_LINKS['vpn'])
        ]
        markup.add(random.choice(promo_buttons))
    
    return markup

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    USERS.add(user_id)
    
    # Daily bonus
    bonus = check_daily_bonus(user_id)
    bonus_msg = f"\n🎁 You got {bonus} bonus point{'s' if bonus > 1 else ''} today!" if bonus else ""
    
    # Referral logic
    if message.text.startswith("/start "):
        ref_id = message.text.split()[1]
        if ref_id.isdigit() and int(ref_id) != user_id:
            ref_id = int(ref_id)
            if ref_id in USERS and user_id not in REFERRALS.get(ref_id, []):
                if ref_id not in REFERRALS:
                    REFERRALS[ref_id] = []
                REFERRALS[ref_id].append(user_id)
                earned = give_points(ref_id, 5)
                bot.send_message(ref_id, f"🎉 User {message.from_user.first_name} joined using your referral link! You earned 5 points. Total: {earned}")
    
    # Track activity
    track_activity(user_id, "start")
    save_data()
    
    welcome_text = f"""
✨ *Welcome to KirmadaTheBot* ✨

Your all-in-one solution for:
• YouTube & Instagram downloads
• PDF creation tools
• Text-to-Speech conversion
• Image effects and more!

Earn rewards by using the bot and referring friends!{bonus_msg}
"""
    
    # Add premium message for non-premium users
    if user_id not in PREMIUM_USERS:
        welcome_text += "\n\n💎 *Upgrade to Premium* to unlock unlimited usage and remove ads! Type /premium for details."
    
    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

# Callback handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == 'youtube':
        bot.send_message(user_id, "🎬 Send a YouTube URL to download video or audio")
    
    elif call.data == 'insta':
        bot.send_message(user_id, "📱 Send Instagram Reel or Post URL")
    
    elif call.data == 'pdf':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Text to PDF", callback_data='text2pdf'))
        markup.add(types.InlineKeyboardButton("Images to PDF", callback_data='img2pdf'))
        markup.add(types.InlineKeyboardButton("Back to Menu", callback_data='menu'))
        bot.send_message(user_id, "Choose a PDF tool:", reply_markup=markup)
    
    elif call.data == 'tts':
        bot.send_message(user_id, "🔊 Send text starting with /speak to convert to voice")
    
    elif call.data == 'image':
        bot.send_message(user_id, "🖼️ Send an image to apply filters and effects")
    
    elif call.data == 'refer':
        link = f"https://t.me/KirmadaTheBot?start={user_id}"
        points = POINTS.get(user_id, 0)
        referrals = len(REFERRALS.get(user_id, []))
        
        # Create share button
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📣 Share Your Link", switch_inline_query=f"Check out this awesome Telegram bot! {link}"))
        markup.add(types.InlineKeyboardButton("📊 View Referral Stats", callback_data='ref_stats'))
        
        bot.send_message(user_id, f"🔗 *Your Referral Link*\n{link}\n\n📊 Stats:\n- Points: {points}\n- Referrals: {referrals}\n\nEarn 5 points for each new user!", parse_mode="Markdown", reply_markup=markup)
    
    elif call.data == 'ref_stats':
        points = POINTS.get(user_id, 0)
        referrals = REFERRALS.get(user_id, [])
        
        if not referrals:
            bot.send_message(user_id, "You haven't referred anyone yet. Share your referral link to start earning points!")
            return
            
        stats = f"🏆 *Your Referral Performance*\n\n- Total Referrals: {len(referrals)}\n- Points Earned: {len(referrals) * 5}\n\n"
        stats += "📈 *Recent Referrals*\n"
        
        # Show last 5 referrals with join date if we had that data
        for i, ref in enumerate(referrals[-5:], 1):
            stats += f"{i}. User ID: {ref}\n"
        
        bot.send_message(user_id, stats, parse_mode="Markdown")
    
    elif call.data == 'points':
        points = POINTS.get(user_id, 0)
        
        # Create redemption buttons
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 Get Premium", callback_data='buy_premium'))
        markup.add(types.InlineKeyboardButton("🛍️ Rewards Shop", callback_data='shop'))
        
        bot.send_message(user_id, f"💰 *Your Points*: {points}\n\nEarn points by:\n- Daily login: +1 point\n- Referrals: +5 points per user\n- Using features: +2 points\n\nPremium users earn 5x daily points!", parse_mode="Markdown", reply_markup=markup)
    
    elif call.data == 'premium':
        premium_status = "✅ ACTIVE" if user_id in PREMIUM_USERS else "❌ INACTIVE"
        
        # Create premium purchase options
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💎 1 Month Premium (100 pts)", callback_data='premium_month'))
        markup.add(types.InlineKeyboardButton("💎💎 1 Year Premium (800 pts)", callback_data='premium_year'))
        markup.add(types.InlineKeyboardButton("Buy Premium (PayPal)", url="https://paypal.me/yourusername"))
        markup.add(types.InlineKeyboardButton("Back to Menu", callback_data='menu'))
        
        benefits = """
✨ *Premium Benefits*:
• No daily usage limits
• No ads/affiliate links
• 5x daily bonus points
• Priority processing
• Exclusive features
• Premium support
        """
        
        bot.send_message(user_id, f"💎 *Premium Status*: {premium_status}\n{benefits}\n\nCurrent Points: {POINTS.get(user_id, 0)}", parse_mode="Markdown", reply_markup=markup)
    
    elif call.data.startswith('premium_'):
        period = call.data.split('_')[1]
        points_needed = 100 if period == 'month' else 800
        
        if POINTS.get(user_id, 0) >= points_needed:
            POINTS[user_id] -= points_needed
            PREMIUM_USERS.add(user_id)
            
            # Set expiration date in a production app
            expiry = "one month" if period == 'month' else "one year"
            
            bot.send_message(user_id, f"🎉 Congratulations! You are now a *Premium Member* for {expiry}!\n\nEnjoy all premium benefits including unlimited usage, no ads, and 5x daily points!", parse_mode="Markdown")
            save_data()
        else:
            bot.send_message(user_id, f"❌ Not enough points! You need {points_needed} points but have {POINTS.get(user_id, 0)}.\n\nEarn more by referring friends or using the bot daily!")
    
    elif call.data == 'shop':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Unlimited Downloads (100pts)", callback_data='buy_unlimited'))
        markup.add(types.InlineKeyboardButton("🚫 Remove Ads (80pts)", callback_data='buy_no_ads'))
        markup.add(types.InlineKeyboardButton("💰 Cash Out via PayPal (500pts)", callback_data='cash_out'))
        markup.add(types.InlineKeyboardButton("🎁 Amazon Gift Card (1000pts)", callback_data='gift_card'))
        markup.add(types.InlineKeyboardButton("Back", callback_data='points'))
        
        bot.send_message(user_id, f"🛍️ *Rewards Shop*\n\nYour Points: {POINTS.get(user_id, 0)}\n\nRedeem your points for valuable rewards!", parse_mode="Markdown", reply_markup=markup)
    
    elif call.data == 'buy_unlimited':
        if POINTS.get(user_id, 0) >= 100:
            POINTS[user_id] -= 100
            # Set unlimited downloads for 7 days
            bot.send_message(user_id, "✅ You've activated unlimited downloads for 7 days! Enjoy!")
            save_data()
        else:
            bot.send_message(user_id, "❌ Not enough points! You need 100 points.")
    
    elif call.data == 'cash_out':
        if POINTS.get(user_id, 0) >= 500:
            bot.send_message(user_id, "💰 To cash out, please contact our admin with your PayPal email address: @admin_username")
        else:
            bot.send_message(user_id, "❌ Not enough points! You need 500 points for cash out.")
    
    elif call.data == 'menu':
        bot.send_message(user_id, "🏠 Main Menu", reply_markup=get_main_menu())
    
    elif call.data == 'text2pdf':
        if not check_user_limits(user_id):
            return bot.send_message(user_id, "⚠️ You've reached your daily limit! Upgrade to Premium for unlimited usage: /premium")
            
        TEMP_STORAGE[user_id] = {'type': 'text2pdf', 'content': []}
        bot.send_message(user_id, "Send multiple text messages to convert into a PDF. Send /done when finished.")
    
    elif call.data == 'img2pdf':
        if not check_user_limits(user_id):
            return bot.send_message(user_id, "⚠️ You've reached your daily limit! Upgrade to Premium for unlimited usage: /premium")
            
        TEMP_STORAGE[user_id] = {'type': 'img2pdf', 'content': []}
        bot.send_message(user_id, "Send multiple photos to convert into a PDF. Send /done when finished.")
    
    elif call.data.startswith('yt_'):
        if not check_user_limits(user_id):
            return bot.send_message(user_id, "⚠️ You've reached your daily limit! Upgrade to Premium for unlimited usage: /premium")
            
        process_youtube_download(user_id, call.data)
    
    elif call.data.startswith('img_'):
        if not check_user_limits(user_id):
            return bot.send_message(user_id, "⚠️ You've reached your daily limit! Upgrade to Premium for unlimited usage: /premium")
            
        effect = call.data.split('_')[1]
        process_image_effect(user_id, effect)
    
    # Clear the callback query
    bot.answer_callback_query(call.id)

# Referral
@bot.message_handler(commands=['refer'])
def refer(message):
    uid = message.from_user.id
    link = f"https://t.me/KirmadaTheBot?start={uid}"
    points = POINTS.get(uid, 0)
    referrals = len(REFERRALS.get(uid, []))
    
    # Create QR code with the referral link
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        qr_path = f"qr_{uid}.png"
        img.save(qr_path)
        
        # Create share button
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📣 Share Your Link", switch_inline_query=f"Check out this awesome Telegram bot! {link}"))
        
        with open(qr_path, 'rb') as qr_file:
            bot.send_photo(
                uid, 
                qr_file, 
                caption=f"🔗 *Your Referral Link*\n{link}\n\n📊 Stats:\n- Points: {points}\n- Referrals: {referrals}\n\nEarn 5 points for each new user! Share this QR code or link with your friends.", 
                parse_mode="Markdown",
                reply_markup=markup
            )
        
        os.remove(qr_path)
    except ImportError:
        # Fallback if qrcode not installed
        bot.reply_to(message, f"🔗 *Your Referral Link*\n{link}\n\n📊 Stats:\n- Points: {points}\n- Referrals: {referrals}\n\nEarn 5 points for each new user!", parse_mode="Markdown")

# YouTube
@bot.message_handler(commands=['youtube'])
def youtube(message):
    bot.reply_to(message, "🎬 Send a YouTube URL to download video or audio")

@bot.message_handler(func=lambda msg: 'youtube.com' in msg.text or 'youtu.be' in msg.text)
def yt_download(message):
    user_id = message.from_user.id
    
    # Check usage limits for non-premium users
    if not check_user_limits(user_id):
        return bot.reply_to(message, "⚠️ You've reached your daily limit! Upgrade to Premium for unlimited usage: /premium")
    
    try:
        url = message.text.strip()
        yt = YouTube(url)
        
        # Track activity
        track_activity(user_id, "youtube_download")
        
        # Create download options markup
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🎬 Video (HD)", callback_data=f"yt_vid_hd_{url}"),
            types.InlineKeyboardButton("🎬 Video (SD)", callback_data=f"yt_vid_sd_{url}")
        )
        markup.add(
            types.InlineKeyboardButton("🎵 Audio Only", callback_data=f"yt_audio_{url}"),
            types.InlineKeyboardButton("Cancel", callback_data="menu")
        )
        
        # Add promotional button with 50% chance for non-premium
        if user_id not in PREMIUM_USERS and random.random() < 0.5:
            markup.add(types.InlineKeyboardButton("🛍️ Premium Music Tools", url=AFFILIATE_LINKS['amazon']))
        
        bot.reply_to(message, f"📹 *{yt.title}*\n\nChoose download format:", parse_mode="Markdown", reply_markup=markup)
        
        # Give points for using the feature
        give_points(user_id, 2)
        
    except Exception as e:
        bot.reply_to(message, f"Error: Could not process YouTube URL. Make sure it's valid.")

def process_youtube_download(user_id, callback_data):
    try:
        # Extract URL and type from callback data
        parts = callback_data.split('_', 3)
        download_type = parts[1]
        quality = parts[2] if len(parts) > 2 else None
        url = parts[3] if len(parts) > 3 else None
        
        if not url:
            return bot.send_message(user_id, "Invalid URL")
            
        yt = YouTube(url)
        status_msg = bot.send_message(user_id, "⏳ Processing your request...")
        
        if download_type == 'vid':
            if quality == 'hd':
                stream = yt.streams.get_highest_resolution()
            else:
                # Get a lower resolution to save bandwidth
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').first()
                
            filename = f"{yt.title.replace('/', '_')[:50]}.mp4"
            stream.download(filename=filename)
            
            # Add affiliate message for non-premium users
            caption = f"🎬 *{yt.title}*"
            if user_id not in PREMIUM_USERS:
                caption += get_affiliate_message()
            else:
                caption += "\n\n✨ *Premium User Download* - Ad-Free"
            
            with open(filename, 'rb') as f:
                bot.send_video(user_id, f, caption=caption, parse_mode="Markdown")
            os.remove(filename)
            
        elif download_type == 'audio':
            # Get audio stream
            stream = yt.streams.filter(only_audio=True).first()
            filename = f"{yt.title.replace('/', '_')[:50]}.mp3"
            stream.download(filename=filename)
            
            # Add affiliate message for non-premium users
            caption = f"🎵 *{yt.title}*"
            if user_id not in PREMIUM_USERS:
                caption += get_affiliate_message()
            else:
                caption += "\n\n✨ *Premium User Download* - Ad-Free"
            
            with open(filename, 'rb') as f:
                bot.send_audio(user_id, f, title=yt.title, caption=caption, parse_mode="Markdown")
            os.remove(filename)
            
        bot.delete_message(user_id, status_msg.message_id)
        
        # Show another feature suggestion
        if random.random() < 0.3:  # 30% chance
            suggestions = [
                "🔊 Try our Text-to-Speech feature with /speak command!",
                "📄 Convert files to PDF with /pdf command!",
                "🖼️ Send an image to apply cool filters!",
                "💰 Check your points balance with /points!"
            ]
            bot.send_message(user_id, random.choice(suggestions))
        
    except Exception as e:
        bot.send_message(user_id, f"Error processing download: {str(e)}")

# Instagram
@bot.message_handler(commands=['insta'])
def insta(message):
    bot.reply_to(message, "📱 Send Instagram Reel or Post URL")

@bot.message_handler(func=lambda msg: 'instagram.com' in msg.text)
def insta_reel(message):
    user_id = message.from_user.id
    
    # Check usage limits for non-premium users
    if not check_user_limits(user_id):
        return bot.reply_to(message, "⚠️ You've reached your daily limit! Upgrade to Premium for unlimited usage: /premium")
    
    try:
        # Track activity
        track_activity(user_id, "instagram_download")
        
        # Create alternative options markup
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 Online Downloader", url="https://instasave.io"))
        markup.add(types.InlineKeyboardButton("📱 Try Instagram App", url="https://play.google.com/store/apps/details?id=com.instagram.android"))
        
        # Add affiliate link for non-premium users
        if user_id not in PREMIUM_USERS:
            markup.add(types.InlineKeyboardButton("🔒 VPN for Instagram", url=AFFILIATE_LINKS['vpn']))
        
        bot.reply_to(
            message, 
            "🔄 Instagram downloading is currently limited on Telegram bots.\n\nTry these alternatives:\n1. Use our web tool: https://instasave.io\n2. Try the /report command if this is important to you",
            reply_markup=markup
        )
        
        # Give points for using the feature
        give_points(user_id, 2)
        
    except Exception as e:
        bot.reply_to(message, "Failed to process Instagram URL")

# PDF Tools
@bot.message_handler(commands=['pdf'])
def pdf(message):
    user_id = message.from_user.id
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Text to PDF", callback_data='text2pdf'))
    markup.add(types.InlineKeyboardButton("Images to PDF", callback_data='img2pdf'))
    
    # Add promotional button for non-premium users
    if user_id not in PREMIUM_USERS:
        markup.add(types.InlineKeyboardButton("📚 Premium PDF Tools", url=AFFILIATE_LINKS['books']))
    
    markup.add(types.InlineKeyboardButton("Back to Menu", callback_data='menu'))
    bot.reply_to(message, "Choose a PDF tool:", reply_markup=markup)

@bot.message_handler(content_types=['text', 'photo'])
def content_collector(message):
    uid = message.from_user.id
    
    # Check if we have special commands first
    if message.content_type == 'text':
        text = message.text.lower()
        if text.startswith('/'):
            return  # Let other handlers process commands
            
        # Handle short greetings
        if text in ['hi', 'hello', 'hey', "what's up", 'sup']:
            return bot.reply_to(message, f"Hey {message.from_user.first_name}! I'm Kirmada~ Your smart helper bot! Use /help for commands.")
    
    # Check if we're collecting content for PDF
    if uid in TEMP_STORAGE:
        if message.content_type == 'text' and TEMP_STORAGE[uid]['type'] == 'text2pdf':
            TEMP_STORAGE[uid]['content'].append(message.text)
            count = len(TEMP_STORAGE[uid]['content'])
            bot.reply_to(message, f"✅ Added text ({count} items).
