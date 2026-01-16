import os
import sys

print("🔍 SETTINGS CHECK KAR RAHA HUN...")

# 1. API ID Check
api_id = os.environ.get("API_ID")
if not api_id:
    print("❌ ERROR: 'API_ID' missing hai!")
    sys.exit(1)
if not api_id.isdigit():
    print(f"❌ ERROR: API_ID mein galti hai! Sirf number hona chahiye. Tune likha hai: {api_id}")
    sys.exit(1)
print("✅ API_ID: OK")

# 2. Bot Token Check
token = os.environ.get("BOT_TOKEN")
if not token:
    print("❌ ERROR: 'BOT_TOKEN' missing hai!")
    sys.exit(1)
if ":" not in token:
    print("❌ ERROR: Bot Token galat lag raha hai (Isme ':' nahi hai).")
    sys.exit(1)
print("✅ BOT_TOKEN: OK")

# 3. Log Channel Check
log_channel = os.environ.get("LOG_CHANNEL")
if not log_channel:
    print("❌ ERROR: 'LOG_CHANNEL' missing hai!")
    sys.exit(1)
if not log_channel.startswith("-100"):
    print(f"❌ ERROR: LOG_CHANNEL galat hai! Ye '-100' se shuru hona chahiye. Tune likha hai: {log_channel}")
    sys.exit(1)
print("✅ LOG_CHANNEL: OK")

# 4. Owner ID Check
owner = os.environ.get("OWNER_ID")
if not owner:
    print("❌ ERROR: 'OWNER_ID' missing hai!")
    sys.exit(1)
print("✅ OWNER_ID: OK")

print("🎉 SAB SETTINGS SAHI HAIN! AB PURANA CODE WAPAS DALO.")
