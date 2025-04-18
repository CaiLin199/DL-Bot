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

def format_progress_bar(current, total):
    try:
        if total <= 0:
            return "[□□□□□□□□□□]", 0, 0
            
        # Calculate sizes in MB
        current_mb = round(current / 1048576, 1)
        total_mb = round(total / 1048576, 1)
        
        # Calculate percentage and ensure it's between 0 and 100
        percentage = min(100, max(0, int((current * 100) / total)))
        
        # Create progress bar
        blocks = min(10, max(0, int(percentage / 10)))
        progress_bar = f"[{'■' * blocks}{'□' * (10 - blocks)}]"
        
        return progress_bar, current_mb, total_mb
    except:
        return "[□□□□□□□□□□]", 0, 0

async def progress_handler(current, total, message, action, last_update):
    try:
        if CANCEL_DOWNLOAD.get(message.chat.id):
            await message.edit("❌ Operation canceled by user.")
            return False

        now = time.time()
        if now - last_update[0] < 5:  # Only update every 5 seconds
            return True

        # Get progress bar and sizes
        progress_bar, current_mb, total_mb = format_progress_bar(current, total)
        
        # Create progress text with consistent format
        progress_text = f"{action}: {progress_bar} {current_mb} Mʙ | {total_mb} Mʙ"
        
        # Update message with progress
        await message.edit(
            progress_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )
        
        last_update[0] = now
        return True
    except:
        return True

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False

    try:
        # Start the download
        download = aria2.add_uris([direct_link])
        gid = download.gid
        status_message = await message.reply(
            "📥 Download started...\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )

        last_update = [0]  # For tracking last progress update time
        while True:
            if CANCEL_DOWNLOAD.get(message.chat.id):
                aria2.remove([gid])
                await status_message.edit("❌ Download canceled by user.")
                return

            download = aria2.get_download(gid)
            if download.is_complete:
                await status_message.edit("✅ Download completed! Preparing to upload...")
                break
            elif download.is_removed:
                await status_message.edit("❌ Download canceled or removed.")
                return
            elif download.has_failed:
                await status_message.edit("❌ Download failed.")
                return

            # Update download progress
            if time.time() - last_update[0] >= 5:
                completed = max(0, download.completed_length)
                total = max(1, download.total_length)
                await progress_handler(completed, total, status_message, "Downloading", last_update)

            time.sleep(1)  # Small delay to prevent CPU overuse

        # Upload the file to Telegram with a thumbnail
        file_path = download.files[0].path
        thumbnail_path = "assist/thumbnail.jpg"
        if os.path.exists(file_path):
            last_update = [0]  # Reset update timer for upload
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
                caption="",
                progress=lambda current, total: progress_handler(
                    current, total, status_message, "Uploading", last_update
                )
            )
            os.remove(file_path)  # Clean up storage
            await status_message.edit("✅ File uploaded and removed from storage.")
        else:
            await status_message.edit("❌ File not found after download.")

    except Exception as e:
        await message.reply(f"❌ Failed to process download: {e}")

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_operation(client, callback_query):
    CANCEL_DOWNLOAD[callback_query.message.chat.id] = True
    await callback_query.answer("Cancellation in progress...")