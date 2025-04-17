import os
from pyrogram import Client, filters
from pyrogram.types import Message
from aria2p import API, Client as Aria2Client
from bot import Bot
from config import OWNER_ID, ARIA2_SECRET, ARIA2_HOST, ARIA2_PORT

# Connect to aria2 RPC server
aria2 = API(
    Aria2Client(
        host=ARIA2_HOST,
        port=ARIA2_PORT,
        secret=ARIA2_SECRET  # Blank if no secret is set
    )
)

@Bot.on_message(filters.command("ddl") & filters.private)
async def direct_downloader(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("You are not authorized to use this command.")
        return

    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]

    try:
        download = aria2.add_uris([direct_link])
        await message.reply(f"Download started with GID: {download.gid}")
    except Exception as e:
        await message.reply(f"Failed to start download: {e}")