import asyncio
from pyrogram import Client, idle

API_ID = 123456
API_HASH = "API_HASH_YAHA_DALO"
BOT_TOKEN = "BOT_TOKEN_YAHA_DALO"

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    await app.start()
    print("Bot started")
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())


