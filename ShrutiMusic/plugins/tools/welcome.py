from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ShrutiMusic.misc import app

# 👉 Yahan apni welcome image ka link daalo
WELCOME_IMAGE = ".  "

@app.on_message(filters.new_chat_members)
async def welcome(client, message):
    for user in message.new_chat_members:
        caption = (
            f"✨ Welcome {user.mention} ✨\n\n"
            f"🎶 Music Lovers Group me aapka swagat hai\n"
            f"🔥 High Quality Songs | ⚡ Fast Play\n\n"
            f"▶️ Song chalane ke liye /play song name likhe\n"
            f"💖 Enjoy & Stay Active"
        )

        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎧 Play Music", callback_data="help_menu"),
                    InlineKeyboardButton("💬 Support", url="https://t.me/shree_update"),
                ],
                [
                    InlineKeyboardButton("📢 Updates Channel", url="https://t.me/shree_update"),
                ],
            ]
        )

        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=caption,
            reply_markup=buttons,
        )        pic = await app.download_media(
            user.photo.big_file_id, file_name=f"pp{user.id}.png"
        )
    except AttributeError:
        pic = "ShrutiMusic/assets/upic.png"

    if (temp.MELCOW).get(f"welcome-{member.chat.id}") is not None:
        try:
            await temp.MELCOW[f"welcome-{member.chat.id}"].delete()
        except Exception as e:
            LOGGER.error(e)

    try:
        welcomeimg = welcomepic(
            pic, user.first_name, member.chat.title, user.id, user.username
        )
        temp.MELCOW[f"welcome-{member.chat.id}"] = await app.send_photo(
            member.chat.id,
            photo=welcomeimg,
            caption=f"""
🌸✨ ──────────────────── ✨🌸

         🎊 <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴏᴜʀ ғᴀᴍɪʟʏ</b> 🎊

🌹 <b>ɴᴀᴍᴇ</b> ➤ {user.mention}
🌺 <b>ᴜsᴇʀɴᴀᴍᴇ</b> ➤ @{user.username if user.username else "ɴᴏᴛ sᴇᴛ"}
🆔 <b>ᴜsᴇʀ ɪᴅ</b> ➤ <code>{user.id}</code>
🏠 <b>ɢʀᴏᴜᴘ</b> ➤ {member.chat.title}

═════════════════════════

💕 <b>ᴡᴇ'ʀᴇ sᴏ ʜᴀᴘᴘʏ ᴛᴏ ʜᴀᴠᴇ ʏᴏᴜ ʜᴇʀᴇ!</b> 
🎵 <b>ᴇɴᴊᴏʏ ᴛʜᴇ ʙᴇsᴛ ᴍᴜsɪᴄ ᴇxᴘᴇʀɪᴇɴᴄᴇ</b> 🎵

✨ <b>ғᴇᴇʟ ғʀᴇᴇ ᴛᴏ sʜᴀʀᴇ ᴀɴᴅ ᴇɴᴊᴏʏ!</b> ✨

<blockquote><b>💝 ᴘᴏᴡᴇʀᴇᴅ ʙʏ ➤ <a href="https://t.me/{app.username}?start=help">Mᴜsɪᴄ ʙᴏᴛs🎶💖</a></b></blockquote>

🌸✨ ──────────────────── ✨🌸
""",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ 🎵", url=f"https://t.me/{app.username}?startgroup=True")]
            ]),
        )

    except Exception as e:
        LOGGER.error(e)

    try:
        os.remove(f"downloads/welcome#{user.id}.png")
        os.remove(f"downloads/pp{user.id}.png")
    except Exception:
        pass


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================
