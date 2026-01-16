import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import UserNotParticipant
import redis
from aiohttp import web
import os
import sys

# --- VARIABLES (Server se uthayega) ---
try:
    API_ID = int(os.environ.get("API_ID"))
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    REDIS_URL = os.environ.get("REDIS_URL")
    OWNER_ID = int(os.environ.get("OWNER_ID"))
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL"))
    FORCE_CHANNEL = os.environ.get("FORCE_CHANNEL") # Bina @ ke username
    PORT = int(os.environ.get("PORT", "8080"))
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    sys.exit(1)

# --- SETUP ---
print("✅ Connecting to Database...")
db = redis.from_url(REDIS_URL, decode_responses=True, ssl_cert_reqs=None)
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- FUNCTIONS ---
def get_points(uid):
    p = db.get(f"user:{uid}:points")
    return int(p) if p else 0

def add_points(uid, amt):
    db.incrby(f"user:{uid}:points", amt)

# --- START ---
@app.on_message(filters.command("start"))
async def start(bot, msg):
    uid = msg.from_user.id
    
    # Force Sub Check
    if FORCE_CHANNEL:
        try:
            await bot.get_chat_member(FORCE_CHANNEL, uid)
        except UserNotParticipant:
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL}")]])
            await msg.reply(f"⚠️ **Access Denied!**\n\nPlease join our channel first.", reply_markup=btn)
            return
        except Exception:
            pass # Admin or Error

    # New User Logic
    if not db.exists(f"user:{uid}:points"):
        db.set(f"user:{uid}:points", 50) # Bonus 50
        # Refer Check
        if len(msg.command) > 1 and msg.command[1].isdigit():
            ref_id = int(msg.command[1])
            if ref_id != uid:
                add_points(ref_id, 50) # Refer Bonus
                try: await bot.send_message(ref_id, "🎉 New Referral! +50 Points")
                except: pass

    # Menu
    menu = ReplyKeyboardMarkup([
        [KeyboardButton("VIDEO 🎬"), KeyboardButton("POINTS 🥇")],
        [KeyboardButton("PROFILE 👤"), KeyboardButton("REFER 🔗")]
    ], resize_keyboard=True)
    
    await msg.reply(f"👋 Welcome **{msg.from_user.first_name}**!", reply_markup=menu)

# --- FEATURES ---
@app.on_message(filters.regex("POINTS 🥇"))
async def pts(bot, m):
    await m.reply(f"🥇 Points: **{get_points(m.from_user.id)}**")

@app.on_message(filters.regex("PROFILE 👤"))
async def prof(bot, m):
    uid = m.from_user.id
    await m.reply(f"👤 **PROFILE**\n🆔 `{uid}`\n💰 Points: {get_points(uid)}")

@app.on_message(filters.regex("REFER 🔗"))
async def refer(bot, m):
    link = f"https://t.me/{bot.me.username}?start={m.from_user.id}"
    await m.reply(f"🔗 **Refer Link:**\n`{link}`\n\nInvite & Earn 50 Points!")

# --- VIDEO LOGIC ---
@app.on_message(filters.chat(LOG_CHANNEL) & filters.video)
async def save_vid(bot, m):
    db.sadd("videos", m.video.file_id)

@app.on_message(filters.regex("VIDEO 🎬"))
async def get_vid(bot, m):
    uid = m.from_user.id
    if get_points(uid) >= 5:
        vid = db.srandmember("videos")
        if vid:
            add_points(uid, -5)
            await m.reply_video(vid, caption="✅ Points: -5")
        else:
            await m.reply("❌ No videos in DB!")
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
