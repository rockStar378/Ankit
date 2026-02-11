import asyncio
from pyrogram import Client, idle

import ShrutiMusic.misc   # module load karne ke liye

API_ID = 123456
API_HASH = "API_HASH"
BOT_TOKEN = "BOT_TOKEN"

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    await app.start()
    print("Bot started successfully")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
