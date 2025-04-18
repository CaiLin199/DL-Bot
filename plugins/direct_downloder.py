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

def create_progress_bar(current, total):
    try:
        if total <= 0:
            return "[□□□□□□□□□□]", 0, 0
            
        current_mb = round(current / 1048576, 1)
        total_mb = round(total / 1048576, 1)
        
        percentage = min(100, max(0, int((current * 100) / total)))
        blocks = min(10, max(0, int(percentage / 10)))
        progress_bar = f"[{'■' * blocks}{'□' * (10 - blocks)}]"
        
        return progress_bar, current_mb, total_mb
    except:
        return "[□□□□□□□□□□]", 0, 0

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False
    last_download_update = 0
    last_upload_update = 0

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

        # Download progress monitoring
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

            current_time = time.time()
            if current_time - last_download_update >= 5:
                try:
                    completed = max(0, download.completed_length)
                    total = max(1, download.total_length)
                    progress_bar, current_mb, total_mb = create_progress_bar(completed, total)
                    
                    await status_message.edit(
                        f"Downloading: {progress_bar} {current_mb} Mʙ | {total_mb} Mʙ",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                        ])
                    )
                    last_download_update = current_time
                except Exception as e:
                    print(f"Download progress error: {str(e)}")

            time.sleep(5)  # Simple sleep instead of asyncio.sleep

        # Handle file upload
        file_path = download.files[0].path
        thumbnail_path = "assist/thumbnail.jpg"
        
        if os.path.exists(file_path):
            # Start the upload
            try:
                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_path,
                    thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
                    caption="",
                    progress=lambda current, total: update_upload_progress(
                        current, total, status_message, message.chat.id
                    )
                )
                os.remove(file_path)
                await status_message.edit("✅ File uploaded and removed from storage.")
            except Exception as e:
                await status_message.edit(f"❌ Upload failed: {str(e)}")
        else:
            await status_message.edit("❌ File not found after download.")

    except Exception as e:
        await message.reply(f"❌ Failed to process: {str(e)}")

# Separate function for upload progress
async def update_upload_progress(current, total, message, chat_id):
    if not hasattr(update_upload_progress, "last_update"):
        update_upload_progress.last_update = 0

    try:
        now = time.time()
        if now - update_upload_progress.last_update < 5:
            return
            
        if CANCEL_DOWNLOAD.get(chat_id):
            return False

        progress_bar, current_mb, total_mb = create_progress_bar(current, total)
        await message.edit(
            f"Uploading: {progress_bar} {current_mb} Mʙ | {total_mb} Mʙ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )
        update_upload_progress.last_update = now
    except Exception as e:
        print(f"Upload progress error: {str(e)}")
    return True

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_dl(_, query):
    CANCEL_DOWNLOAD[query.message.chat.id] = True
    await query.answer("Cancelling...")