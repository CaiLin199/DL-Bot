import os
import time
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aria2p import API, Client as Aria2Client
from bot import Bot
from config import OWNER_ID, ARIA2_SECRET, ARIA2_HOST, ARIA2_PORT

# Connect to aria2 RPC server
aria2 = API(
    Aria2Client(
        host=ARIA2_HOST,
        port=ARIA2_PORT,
        secret=ARIA2_SECRET
    )
)

CANCEL_DOWNLOAD = {}

def make_progress_bar(current, total):
    if total == 0:
        total = 1
    percentage = current * 100 // total
    digits = min(10, max(0, percentage // 10))
    return f"[{'■' * digits}{'□' * (10 - digits)}]"

async def progress(current, total, message, type_of_ps):
    if message.chat.id not in CANCEL_DOWNLOAD:
        CANCEL_DOWNLOAD[message.chat.id] = False
        
    if CANCEL_DOWNLOAD[message.chat.id]:
        aria2.remove(message.id)
        await message.edit("❌ Download Cancelled")
        return False
        
    try:
        # Simple progress calculation that won't affect speed
        bar = make_progress_bar(current, total)
        percentage = current * 100 // total if total > 0 else 0
        current_mb = round(current / 1048576, 2)
        total_mb = round(total / 1048576, 2)
        
        await message.edit(
            f"{type_of_ps}: {bar} {current_mb}/{total_mb} MB",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Cancel", callback_data="cancel")
            ]])
        )
    except Exception as e:
        pass  # Silently handle any message edit errors
    return True

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False

    try:
        download = aria2.add_uris([direct_link])
        gid = download.gid
        status_message = await message.reply("📥 Starting Download...")

        while True:
            download = aria2.get_download(gid)
            if download.is_complete:
                await status_message.edit("✅ Download Complete! Starting Upload...")
                break
            elif download.has_failed:
                await status_message.edit("❌ Download Failed!")
                return
            elif CANCEL_DOWNLOAD.get(message.chat.id):
                aria2.remove([gid])
                await status_message.edit("❌ Download Cancelled!")
                return

            total = download.total_length
            completed = download.completed_length
            await progress(completed, total, status_message, "Downloading")
            time.sleep(5)  # Update every 5 seconds without affecting speed

        file_path = download.files[0].path
        if os.path.exists(file_path):
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                progress=progress,
                progress_args=(status_message, "Uploading")
            )
            os.remove(file_path)
            await status_message.edit("✅ Process Completed!")
        else:
            await status_message.edit("❌ File Not Found!")

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_dl(_, query):
    CANCEL_DOWNLOAD[query.message.chat.id] = True
    await query.answer("Cancelling...")