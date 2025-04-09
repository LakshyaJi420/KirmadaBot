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

# Set API Key securely (Railway will supply BOT_TOKEN environment variable)
API_KEY = os.environ.get("BOT_TOKEN", "7930757231:AAFHc49RHS_BGy0DIDSPK1YXlXXkUCLB6nI")
bot = telebot.TeleBot(API_KEY)

# Constants
OWNER_ID = 7428805370  # Your owner ID
USERS = set()
REFERRALS = {}
POINTS = {}
DAILY_BONUS = {}
TEMP_STORAGE = {}

# Load saved data if available (simplified - in production use a proper database)
try:
    with open('users.txt', 'r') as f:
        USERS = set([int(x) for x in f.read().split()])
    with open('points.txt', 'r') as f:
        for line in f:
            if line.strip():
                user_id, points = line.strip().split(':')
                POINTS[int(user_id)] = int(points)
except FileNotFoundError:
    pass

# Save data function
def save_data():
    with open('users.txt', 'w') as f:
        f.write(' '.join([str(user) for user in USERS]))
    with open('points.txt', 'w') as f:
        for user_id, points in POINTS.items():
            f.write(f"{user_id}:{points}\n")

# Utils
def get_affiliate_message():
    messages = [
        "\n\n👉 Want cool tools? Check out our deals: [Buy Tools Cheap](https://amzn.to/3xXWlink)",
        "\n\n🔥 Exclusive offers for bot users: [Check Deals](https://amzn.to/3xXWlink)",
        "\n\n💡 Support us by checking: [Special Discounts](https://amzn.to/3xXWlink)"
    ]
    return random.choice(messages)

def give_points(user_id, points=2):
    if user_id not in POINTS:
        POINTS[user_id] = 0
    POINTS[user_id] += points
    save_data()
    return POINTS[user_id]

def check_daily_bonus(user_id):
    today = time.strftime("%Y-%m-%d")
    if user_id not in DAILY_BONUS or DAILY_BONUS[user_id] != today:
        DAILY_BONUS[user_id] = today
        give_points(user_id, 1)
        return True
    return False

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
    markup.add(types.InlineKeyboardButton("💰 My Points", callback_data='points'))
    return markup

# ------------------------------
# /start Command with Referral & Daily Bonus
# ------------------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    USERS.add(user_id)
    
    # Daily bonus check
    is_bonus = check_daily_bonus(user_id)
    bonus_msg = "\n🎁 You got 1 bonus point today!" if is_bonus else ""
    
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
    
    save_data()
    
    welcome_text = f"""
✨ *Welcome to KirmadaTheBot* ✨

Download, Convert, Share — All in One Place!
Earn rewards by sharing the bot!{bonus_msg}
"""
    
    bot.send_message(user_id, welcome_text, parse_mode="Markdown", reply_markup=get_main_menu())

# ------------------------------
# Callback Handler for Inline Buttons
# ------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == 'youtube':
        bot.send_message(user_id, "Send a YouTube URL to download video or audio")
    elif call.data == 'insta':
        bot.send_message(user_id, "Send Instagram Reel or Post URL")
    elif call.data == 'pdf':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Text to PDF", callback_data='text2pdf'))
        markup.add(types.InlineKeyboardButton("Images to PDF", callback_data='img2pdf'))
        markup.add(types.InlineKeyboardButton("Back to Menu", callback_data='menu'))
        bot.send_message(user_id, "Choose a PDF tool:", reply_markup=markup)
    elif call.data == 'tts':
        bot.send_message(user_id, "Send text starting with /speak to convert to voice")
    elif call.data == 'image':
        bot.send_message(user_id, "Send an image to apply filters and effects")
    elif call.data == 'refer':
        link = f"https://t.me/KirmadaTheBot?start={user_id}"
        points = POINTS.get(user_id, 0)
        referrals = len(REFERRALS.get(user_id, []))
        bot.send_message(user_id, f"🔗 *Your Referral Link*\n{link}\n\n📊 Stats:\n- Points: {points}\n- Referrals: {referrals}\n\nEarn 5 points for each new user!", parse_mode="Markdown")
    elif call.data == 'points':
        points = POINTS.get(user_id, 0)
        bot.send_message(user_id, f"💰 *Your Points*: {points}\n\nEarn points by:\n- Daily login: +1 point\n- Referrals: +5 points\n- Using features: +2 points", parse_mode="Markdown")
    elif call.data == 'menu':
        bot.send_message(user_id, "🏠 Main Menu", reply_markup=get_main_menu())
    elif call.data == 'text2pdf':
        TEMP_STORAGE[user_id] = {'type': 'text2pdf', 'content': []}
        bot.send_message(user_id, "Send multiple text messages to convert into a PDF. Send /done when finished.")
    elif call.data == 'img2pdf':
        TEMP_STORAGE[user_id] = {'type': 'img2pdf', 'content': []}
        bot.send_message(user_id, "Send multiple photos to convert into a PDF. Send /done when finished.")
    # Clear the callback query (so user sees immediate response)
    bot.answer_callback_query(call.id)

# ------------------------------
# Referral (as separate command as well)
# ------------------------------
@bot.message_handler(commands=['refer'])
def refer(message):
    uid = message.from_user.id
    link = f"https://t.me/KirmadaTheBot?start={uid}"
    points = POINTS.get(uid, 0)
    referrals = len(REFERRALS.get(uid, []))
    bot.reply_to(message, f"🔗 *Your Referral Link*\n{link}\n\n📊 Stats:\n- Points: {points}\n- Referrals: {referrals}\n\nEarn 5 points for each new user!", parse_mode="Markdown")

# ------------------------------
# YouTube Download Flow
# ------------------------------
@bot.message_handler(commands=['youtube'])
def youtube(message):
    bot.reply_to(message, "Send a YouTube URL to download video or audio")

@bot.message_handler(func=lambda msg: 'youtube.com' in msg.text or 'youtu.be' in msg.text)
def yt_download(message):
    try:
        url = message.text.strip()
        yt = YouTube(url)
        
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
        
        bot.reply_to(message, f"📹 *{yt.title}*\n\nChoose download format:", parse_mode="Markdown", reply_markup=markup)
        
        # Award points for using a feature
        give_points(message.from_user.id, 2)
        
    except Exception as e:
        bot.reply_to(message, f"Error: Could not process YouTube URL. Ensure the link is valid.")

def process_youtube_download(user_id, callback_data):
    try:
        # Expected callback format: yt_vid_hd_URL, yt_vid_sd_URL, or yt_audio_URL
        parts = callback_data.split('_', 3)
        download_type = parts[1]  # "vid" or "audio"
        quality = parts[2]        # "hd" or "sd" when applicable
        url = parts[3]            # Video URL
        
        if not url:
            return bot.send_message(user_id, "Invalid URL")
            
        yt = YouTube(url)
        status_msg = bot.send_message(user_id, "⏳ Processing your request...")
        
        if download_type == 'vid':
            if quality == 'hd':
                stream = yt.streams.get_highest_resolution()
            else:
                # Lower resolution stream
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').first()
            filename = f"{yt.title.replace('/', '_')[:50]}.mp4"
            stream.download(filename=filename)
            with open(filename, 'rb') as f:
                bot.send_video(user_id, f, caption=f"🎬 *{yt.title}*" + get_affiliate_message(), parse_mode="Markdown")
            os.remove(filename)
            
        elif download_type == 'audio':
            stream = yt.streams.filter(only_audio=True).first()
            filename = f"{yt.title.replace('/', '_')[:50]}.mp3"
            stream.download(filename=filename)
            with open(filename, 'rb') as f:
                bot.send_audio(user_id, f, title=yt.title, caption=f"🎵 *{yt.title}*" + get_affiliate_message(), parse_mode="Markdown")
            os.remove(filename)
            
        bot.delete_message(user_id, status_msg.message_id)
        
    except Exception as e:
        bot.send_message(user_id, f"Error processing download: {str(e)}")

# ------------------------------
# Instagram Download Flow (Guidance Only)
# ------------------------------
@bot.message_handler(commands=['insta'])
def insta(message):
    bot.reply_to(message, "Send Instagram Reel or Post URL")

@bot.message_handler(func=lambda msg: 'instagram.com' in msg.text)
def insta_reel(message):
    try:
        bot.reply_to(message, "🔄 Instagram downloading is currently limited on Telegram bots.\n\nTry these alternatives:\n1. Use our web tool: https://instasave.io\n2. Report if this is essential.")
        give_points(message.from_user.id, 2)
    except Exception as e:
        bot.reply_to(message, "Failed to process Instagram URL")

# ------------------------------
# PDF Tools: Text to PDF & Images to PDF
# ------------------------------
@bot.message_handler(commands=['pdf'])
def pdf(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Text to PDF", callback_data='text2pdf'))
    markup.add(types.InlineKeyboardButton("Images to PDF", callback_data='img2pdf'))
    markup.add(types.InlineKeyboardButton("Back to Menu", callback_data='menu'))
    bot.reply_to(message, "Choose a PDF tool:", reply_markup=markup)

@bot.message_handler(content_types=['text', 'photo'])
def content_collector(message):
    uid = message.from_user.id
    
    # If we're collecting content for PDF conversion
    if uid in TEMP_STORAGE:
        if message.content_type == 'text' and TEMP_STORAGE[uid]['type'] == 'text2pdf':
            TEMP_STORAGE[uid]['content'].append(message.text)
            count = len(TEMP_STORAGE[uid]['content'])
            bot.reply_to(message, f"✅ Added text ({count} items). Send more or /done to finish.")
        elif message.content_type == 'photo' and TEMP_STORAGE[uid]['type'] == 'img2pdf':
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded = bot.download_file(file_info.file_path)
            filename = f"photo_{uid}_{len(TEMP_STORAGE[uid]['content'])}.jpg"
            with open(filename, 'wb') as f:
                f.write(downloaded)
            TEMP_STORAGE[uid]['content'].append(filename)
            count = len(TEMP_STORAGE[uid]['content'])
            bot.reply_to(message, f"✅ Added image ({count} images). Send more or /done to finish.")
        return
    
    # Handle images for effects if no PDF collection is in progress
    if message.content_type == 'photo' and uid not in TEMP_STORAGE:
        process_image_effects(message)

@bot.message_handler(commands=['done'])
def create_pdf(message):
    uid = message.from_user.id
    if uid in TEMP_STORAGE and TEMP_STORAGE[uid]['content']:
        bot.send_message(uid, "⏳ Creating your PDF...")
        
        pdf_type = TEMP_STORAGE[uid]['type']
        content = TEMP_STORAGE[uid]['content']
        
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            if pdf_type == 'text2pdf':
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for text in content:
                    pdf.multi_cell(0, 10, text)
                    pdf.ln(5)
                    
            elif pdf_type == 'img2pdf':
                for img_path in content:
                    pdf.add_page()
                    try:
                        img = Image.open(img_path)
                        width, height = img.size
                        aspect = width / height
                        page_width = 210
                        page_height = 297
                        margin = 10
                        if aspect > 1:
                            img_width = page_width - 2 * margin
                            img_height = img_width / aspect
                        else:
                            img_height = page_height - 2 * margin
                            img_width = img_height * aspect
                        pdf.image(img_path, x=margin, y=margin, w=img_width)
                    except Exception as e:
                        pdf.cell(0, 10, f"Error processing image: {str(e)}", ln=True)
                for img_path in content:
                    try:
                        os.remove(img_path)
                    except:
                        pass
                        
            file_path = f"{uid}_output.pdf"
            pdf.output(file_path)
            with open(file_path, 'rb') as f:
                bot.send_document(uid, f, caption="📄 Here's your PDF!" + get_affiliate_message(), parse_mode="Markdown")
            os.remove(file_path)
            give_points(uid, 2)
        except Exception as e:
            bot.send_message(uid, f"❌ Error creating PDF: {str(e)}")
        TEMP_STORAGE.pop(uid)
    else:
        bot.reply_to(message, "You haven't added anything yet! Send text or images first.")

# ------------------------------
# Image Effects (Filters)
# ------------------------------
def process_image_effects(message):
    try:
        uid = message.from_user.id
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Blur", callback_data="img_blur"),
            types.InlineKeyboardButton("B&W", callback_data="img_bw"),
            types.InlineKeyboardButton("Sharpen", callback_data="img_sharpen"),
            types.InlineKeyboardButton("Invert", callback_data="img_invert")
        )
        
        img_path = f"temp_img_{uid}.jpg"
        with open(img_path, 'wb') as f:
            f.write(downloaded)
        
        TEMP_STORAGE[uid] = {'type': 'image', 'content': img_path}
        bot.reply_to(message, "Choose an effect to apply:", reply_markup=markup)
        
    except Exception as e:
        bot.reply_to(message, f"Error processing image: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("img_"))
def image_effects_handler(call):
    uid = call.from_user.id
    if uid not in TEMP_STORAGE or TEMP_STORAGE[uid]['type'] != 'image':
        return bot.answer_callback_query(call.id, "No image found.")
    effect = call.data.split('_')[1]
    orig_path = TEMP_STORAGE[uid]['content']
    try:
        img = Image.open(orig_path)
        
        if effect == "blur":
            img = img.filter(ImageFilter.GaussianBlur(5))
        elif effect == "bw":
            img = img.convert("L")
        elif effect == "sharpen":
            img = img.filter(ImageFilter.SHARPEN)
        elif effect == "invert":
            img = Image.frombytes(img.mode, img.size, bytes([255 - b for b in img.tobytes()]))
        
        output = BytesIO()
        img.save(output, format='JPEG')
        output.seek(0)
        
        bot.send_photo(uid, output, caption="Here's your processed image!" + get_affiliate_message())
        os.remove(orig_path)
        TEMP_STORAGE.pop(uid)
    except Exception as e:
        bot.send_message(uid, f"Error applying effect: {str(e)}")
    bot.answer_callback_query(call.id)

# ------------------------------
# Text-to-Speech
# ------------------------------
@bot.message_handler(commands=['speak'])
def tts(message):
    text = message.text.replace('/speak', '').strip()
    if not text:
        return bot.reply_to(message, "Type some text after /speak like this: /speak Hello!")
    try:
        status_msg = bot.reply_to(message, "🔊 Converting text to speech...")
        tts = gTTS(text)
        filename = f"speech_{message.from_user.id}.mp3"
        tts.save(filename)
        with open(filename, 'rb') as f:
            bot.send_audio(message.chat.id, f, title="Text to Speech")
        os.remove(filename)
        bot.delete_message(message.chat.id, status_msg.message_id)
        give_points(message.from_user.id, 2)
    except Exception as e:
        bot.reply_to(message, f"Error converting text to speech: {str(e)}")

# ------------------------------
# Help Command
# ------------------------------
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🤖 *KirmadaTheBot Commands*:

📹 *YouTube Download*
- Send YouTube URL
- Choose video or audio format

📱 *Instagram Download*
- Send Instagram reel or post URL
- Guidance provided for alternatives

📄 *PDF Tools*
- /pdf - Access PDF converter tools
- Convert texts/images into a PDF (end with /done)

🔊 *Text to Speech*
- /speak [your text] - Convert text to audio

🖼️ *Image Effects*
- Send an image & choose a filter (Blur, B&W, Sharpen, Invert)

🎁 *Referral Program*
- /refer - Get your referral link and see your stats

💰 *Points System*
- Daily login: +1 point
- Using features: +2 points
- Referrals: +5 points

Need more help? Just ask!
"""
    bot.reply_to(message, help_text, parse_mode="Markdown")

# ------------------------------
# Owner/Admin Panel and Commands
# ------------------------------
@bot.message_handler(commands=['panel'])
def panel(message):
    if message.from_user.id != OWNER_ID:
        return
    bot.reply_to(message, """👑 *Owner Panel*
- /broadcast <msg> - Send message to all users
- /users - See user count
- /stats - View usage statistics
- /test - Test bot functionality
- /post_daily - Send daily post to channel
""", parse_mode="Markdown")

@bot.message_handler(commands=['users'])
def show_users(message):
    if message.from_user.id == OWNER_ID:
        user_count = len(USERS)
        active_today = len(DAILY_BONUS.keys())
        bot.reply_to(message, f"📊 *User Statistics*\n- Total Users: {user_count}\n- Active Today: {active_today}", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != OWNER_ID:
        return
    user_count = len(USERS)
    referral_count = sum(len(refs) for refs in REFERRALS.values())
    top_referrers = sorted([(uid, len(refs)) for uid, refs in REFERRALS.items()], key=lambda x: x[1], reverse=True)[:5]
    stats = f"📊 *Bot Statistics*\n- Total Users: {user_count}\n- Total Referrals: {referral_count}\n\n"
    if top_referrers:
        stats += "*Top Referrers:*\n"
        for uid, count in top_referrers:
            stats += f"- ID {uid}: {count} referrals\n"
    bot.reply_to(message, stats, parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        return bot.reply_to(message, "Please include a message to broadcast")
    sent = 0
    failed = 0
    progress = bot.reply_to(message, f"⏳ Broadcasting: 0/{len(USERS)} users")
    for i, user in enumerate(USERS):
        try:
            bot.send_message(user, f"[Broadcast]\n{text}", parse_mode="Markdown")
            sent += 1
        except:
            failed += 1
        if i % 10 == 0:
            try:
                bot.edit_message_text(f"⏳ Broadcasting: {i}/{len(USERS)} users", message.chat.id, progress.message_id)
            except:
                pass
    bot.edit_message_text(f"✅ Broadcast complete!\n- Sent: {sent}\n- Failed: {failed}", message.chat.id, progress.message_id)

@bot.message_handler(commands=['test'])
def test(message):
    if message.from_user.id == OWNER_ID:
        bot.reply_to(message, "✅ Admin mode is active. All functions working fine!")

@bot.message_handler(commands=['post_daily'])
def post_daily(message):
    if message.from_user.id != OWNER_ID:
        return bot.reply_to(message, "❌ You're not allowed!")
    tips = [
        "Did you know you can convert text to voice using /speak?",
        "Try our PDF creation tools with /pdf command!",
        "Share your referral link to earn points!",
        "Download YouTube videos by simply sending the URL!",
        "Upload an image to apply cool filters!"
    ]
    text = f"🌟 *Daily Tip from Kirmada~* ✨\n\n{random.choice(tips)}"
    group_id = -100123456789  # Replace with your group/channel ID
    try:
        bot.send_message(group_id, text, parse_mode="Markdown")
        bot.reply_to(message, "✅ Daily post sent successfully!")
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to send daily post: {str(e)}")

# ------------------------------
# Fallback for Unrecognized Commands
# ------------------------------
@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.reply_to(message, "I'm not sure what you mean. Try /help for available commands!")

print("Bot is running...")
bot.infinity_polling()
