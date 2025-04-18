import os
import time
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aria2p import API, Client as Aria2Client
from bot import Bot
from config import OWNER_ID, ARIA2_SECRET, ARIA2_HOST, ARIA2_PORT

# Your existing aria2 setup remains the same
aria2 = API(
    Aria2Client(
        host=ARIA2_HOST,
        port=ARIA2_PORT,
        secret=ARIA2_SECRET
    )
)

CANCEL_DOWNLOAD = {}

def create_progress_bar(current, total):
    percentage = current * 100 // total
    completed_blocks = "■" * (percentage // 10)
    remaining_blocks = "□" * (10 - (percentage // 10))
    return f"[{completed_blocks}{remaining_blocks}]"

async def progress_bar(current, total, status_message, last_update):
    if CANCEL_DOWNLOAD.get(status_message.chat.id):
        await status_message.edit("❌ Upload canceled by user.")
        return False

    current_time = time.time()
    if current_time - last_update[0] >= 5:  # 5-second delay between updates
        # Calculate sizes in MB
        current_mb = round(current / 1048576, 1)
        total_mb = round(total / 1048576, 1)
        
        # Create progress bar
        progress_bar = create_progress_bar(current, total)
        
        # Create progress text
        progress_text = f"Uploading: {progress_bar} {current_mb} Mʙ | {total_mb} Mʙ"
        
        await status_message.edit(
            progress_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )
        last_update[0] = current_time
    return True

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    
    if len(message.command) < 2:        
        return

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False

    try:
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

            current_time = time.time()
            if current_time - last_update[0] >= 5:  # 5-second delay
                completed = download.completed_length
                total = download.total_length
                
                # Create download progress bar
                progress_bar = create_progress_bar(completed, total)
                current_mb = round(completed / 1048576, 1)
                total_mb = round(total / 1048576, 1)
                
                progress_text = f"Downloading: {progress_bar} {current_mb} Mʙ | {total_mb} Mʙ"
                await status_message.edit(
                    progress_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                    ])
                )
                last_update[0] = current_time
            
            time.sleep(1)  # Small delay to prevent CPU overuse

        file_path = download.files[0].path
        thumbnail_path = "assist/thumbnail.jpg"
        if os.path.exists(file_path):
            last_update = [0]  # Reset update timer for upload
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
                caption="",
                progress=lambda current, total: progress_bar(current, total, status_message, last_update)
            )
            os.remove(file_path)
            await status_message.edit("✅ File uploaded and removed from storage.")
        else:
            await status_message.edit("❌ File not found after download.")

    except Exception as e:
        await message.reply(f"❌ Failed to process download: {e}")

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_operation(client, callback_query):
    CANCEL_DOWNLOAD[callback_query.message.chat.id] = True
    await callback_query.answer("Cancellation in progress...")