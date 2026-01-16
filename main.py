import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import UserNotParticipant
import sqlite3
from aiohttp import web
import os
import sys

# ==========================================
# 👇 SETTINGS (Jo tune test ki thi)
# ==========================================
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))
FORCE_CHANNEL = os.environ.get("FORCE_CHANNEL", "None") # Agar nahi chahiye to None likh dena
PORT = int(os.environ.get("PORT", 8080))

# ==========================================
# 📂 INTERNAL DATABASE (No Internet Needed)
# ==========================================
# Ye file Render ke andar banegi, bahar connect nahi karegi
conn = sqlite3.connect('mybot.db', check_same_thread=False)
cur = conn.cursor()

# Tables banana
cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS videos (file_id TEXT PRIMARY KEY)")
conn.commit()

print("✅ DATABASE READY!")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- DATABASE FUNCTIONS ---
def get_points(uid):
    cur.execute("SELECT points FROM users WHERE user_id = ?", (uid,))
    res = cur.fetchone()
    return res[0] if res else 0

def add_points(uid, amt):
    cur.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?, 0)", (uid,))
    cur.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amt, uid))
    conn.commit()

def save_video(file_id):
    try:
        cur.execute("INSERT OR IGNORE INTO videos (file_id) VALUES (?)", (file_id,))
        conn.commit()
    except: pass

def get_random_video():
    cur.execute("SELECT file_id FROM videos ORDER BY RANDOM() LIMIT 1")
    res = cur.fetchone()
    return res[0] if res else None

# --- BOT COMMANDS ---
@app.on_message(filters.command("start"))
async def start(bot, msg):
    uid = msg.from_user.id

    # Force Sub Check (Safe Mode)
    if FORCE_CHANNEL and FORCE_CHANNEL.lower() != "none":
        try:
            await bot.get_chat_member(FORCE_CHANNEL, uid)
        except UserNotParticipant:
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL}")]])
            await msg.reply("🚫 **Access Denied!**\nPlease join our channel first.", reply_markup=btn)
            return
        except Exception as e:
            print(f"Force Sub Error (Ignore): {e}")

    # User Register
    cur.execute("SELECT 1 FROM users WHERE user_id = ?", (uid,))
    if not cur.fetchone():
        add_points(uid, 50) # Welcome Bonus
        # Referral
        if len(msg.command) > 1 and msg.command[1].isdigit():
            ref = int(msg.command[1])
            if ref != uid:
                add_points(ref, 20)
                try: await bot.send_message(ref, "🎉 Referral Bonus: +20 Points")
                except: pass

    menu = ReplyKeyboardMarkup([
        [KeyboardButton("VIDEO 🎬"), KeyboardButton("POINTS 🥇")],
        [KeyboardButton("PROFILE 👤"), KeyboardButton("REFER 🔗")]
    ], resize_keyboard=True)
    
    await msg.reply(f"👋 Welcome **{msg.from_user.first_name}**!", reply_markup=menu)

@app.on_message(filters.regex("POINTS 🥇"))
async def pts(bot, m):
    await m.reply(f"🥇 Points: **{get_points(m.from_user.id)}**")

@app.on_message(filters.regex("PROFILE 👤"))
async def prof(bot, m):
    uid = m.from_user.id
    await m.reply(f"👤 **PROFILE**\n🆔 `{uid}`\n💰 Balance: {get_points(uid)}")

@app.on_message(filters.regex("REFER 🔗"))
async def refer(bot, m):
    link = f"https://t.me/{bot.me.username}?start={m.from_user.id}"
    await m.reply(f"🔗 **Refer Link:**\n`{link}`\n\nInvite Friends & Earn Points!")

# --- VIDEO SYSTEM ---
@app.on_message(filters.chat(LOG_CHANNEL) & filters.video)
async def auto_save(bot, m):
    save_video(m.video.file_id)

@app.on_message(filters.regex("VIDEO 🎬"))
async def send_vid(bot, m):
    uid = m.from_user.id
    if get_points(uid) >= 5:
        vid = get_random_video()
        if vid:
            add_points(uid, -5)
            await m.reply_video(vid, caption="✅ Points: -5")
        else:
            await m.reply("❌ No videos in Database! (Admin needs to upload to Log Channel)")
    else:
        await m.reply("❌ Low Balance! Need 5 Points.")

# --- 🌐 FAKE WEB SERVER (To Keep Render Alive) ---
async def web_server():
    async def handle(req):
        return web.Response(text="Bot is Running Successfully!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    print(f"🌍 Web Server Started on Port {PORT}")

# --- MAIN ---
async def main():
    await web_server() # Server start
    print("🚀 Starting Bot...")
    await app.start()
    print("✅ BOT IS LIVE!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
