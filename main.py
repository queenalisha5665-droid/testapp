import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import UserNotParticipant
import psycopg2
from aiohttp import web
import os
import sys

# ==========================================
# 👇 SETTINGS (Server se lega)
# ==========================================
try:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    DATABASE_URL = os.environ.get("DATABASE_URL") # Supabase wala link
    OWNER_ID = int(os.environ.get("OWNER_ID"))
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))
    FORCE_CHANNEL = os.environ.get("FORCE_CHANNEL")
    PORT = int(os.environ.get("PORT", 8080))
except:
    print("❌ Variables Missing! Render Settings check karo.")
    sys.exit(1)

# ==========================================
# 🔌 DATABASE CONNECTION (PostgreSQL)
# ==========================================
print("🔄 Connecting to Supabase...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 🛠️ AUTO CREATE TABLES (Agar nahi hai to bana dega)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            points INT DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS videos (
            id SERIAL PRIMARY KEY,
            file_id TEXT UNIQUE
        );
    """)
    print("✅ Database Connected & Tables Ready!")
except Exception as e:
    print(f"❌ Database Error: {e}")
    sys.exit(1)

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- DATABASE FUNCTIONS ---
def get_points(uid):
    cur.execute("SELECT points FROM users WHERE user_id = %s", (uid,))
    result = cur.fetchone()
    return result[0] if result else 0

def add_points(uid, amt):
    # Upsert Logic (Insert agar naya hai, Update agar purana hai)
    cur.execute("""
        INSERT INTO users (user_id, points) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET points = users.points + %s
    """, (uid, amt, amt))

def save_video_db(file_id):
    try:
        cur.execute("INSERT INTO videos (file_id) VALUES (%s) ON CONFLICT DO NOTHING", (file_id,))
    except: pass

def get_random_video():
    # SQL Command random row nikalne ke liye
    cur.execute("SELECT file_id FROM videos ORDER BY RANDOM() LIMIT 1")
    res = cur.fetchone()
    return res[0] if res else None

# --- BOT LOGIC ---
@app.on_message(filters.command("start"))
async def start(bot, msg):
    uid = msg.from_user.id

    # Force Sub
    if FORCE_CHANNEL and FORCE_CHANNEL.lower() != "none":
        try:
            await bot.get_chat_member(FORCE_CHANNEL, uid)
        except UserNotParticipant:
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL}")]])
            await msg.reply("🚫 **Access Denied!**\nJoin channel first.", reply_markup=btn)
            return
        except: pass

    # New User Check
    cur.execute("SELECT 1 FROM users WHERE user_id = %s", (uid,))
    if not cur.fetchone():
        add_points(uid, 50) # Welcome Bonus
        # Refer System
        if len(msg.command) > 1 and msg.command[1].isdigit():
            ref = int(msg.command[1])
            if ref != uid:
                add_points(ref, 20)
                try: await bot.send_message(ref, "🎉 New Referral! +20 Points")
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
    await m.reply(f"🔗 **Refer Link:**\n`{link}`\n\nReward: +20 Points")

@app.on_message(filters.chat(LOG_CHANNEL) & filters.video)
async def saver(bot, m):
    save_video_db(m.video.file_id)

@app.on_message(filters.regex("VIDEO 🎬"))
async def get_vid(bot, m):
    uid = m.from_user.id
    if get_points(uid) >= 5:
        vid = get_random_video()
        if vid:
            add_points(uid, -5)
            await m.reply_video(vid, caption="✅ Points: -5")
        else:
            await m.reply("❌ No videos in Database!")
    else:
        await m.reply("❌ Low Balance! Need 5 Points.")

# --- WEB SERVER ---
async def web_server():
    async def handle(req): return web.Response(text="Bot Running")
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()

async def main():
    await web_server()
    await app.start()
    print("✅ Bot Started!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
