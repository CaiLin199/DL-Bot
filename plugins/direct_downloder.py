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
        secret=ARIA2_SECRET  # Leave blank if no secret is set
    )
)

# Global variable to track cancellation
CANCEL_DOWNLOAD = {}

# Reusable progress bar function with a 5-second delay
async def progress_bar(current, total, status_message, last_update):
    if CANCEL_DOWNLOAD.get(status_message.chat.id):  # Check if cancellation was requested
        await status_message.edit("❌ Upload canceled by user.")
        return False  # Stop the upload

    # Calculate progress in MB
    progress = round(current / 1024 / 1024, 1)
    total_mb = round(total / 1024 / 1024, 1)
    progress_text = f"Uploading: {progress}/{total_mb} MB"

    # Update every 5 seconds only
    current_time = time.time()
    if current_time - last_update[0] >= 5:  # Check if 5 seconds have passed since the last update
        await status_message.edit(progress_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        ))
        last_update[0] = current_time  # Update the last update time
    return True

@Bot.on_message(filters.command("ddl") & filters.private)
async def direct_downloader(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("You are not authorized to use this command.")
        return

    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False  # Initialize cancel flag

    try:
        # Start the download
        download = aria2.add_uris([direct_link])
        gid = download.gid
        status_message = await message.reply(f"📥 Download started with GID: {gid}...\n", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        ))

        # Monitor the download progress
        while True:
            if CANCEL_DOWNLOAD.get(message.chat.id):  # Check if cancellation was requested
                aria2.remove([gid])  # Cancel the download in aria2
                await status_message.edit("❌ Download canceled by user.")
                return

            download = aria2.get_download(gid)
            if download.is_complete:
                await status_message.edit("✅ Download completed! Preparing to upload to Telegram...")
                break
            elif download.is_removed:
                await status_message.edit("❌ Download canceled or removed.")
                return
            elif download.has_failed:
                await status_message.edit("❌ Download failed.")
                return

            completed = download.completed_length
            total = download.total_length
            speed = download.download_speed

            # Fix for ETA handling
            if download.eta is not None:
                if isinstance(download.eta, int):
                    eta = str(timedelta(seconds=download.eta))
                else:
                    eta = str(download.eta)
            else:
                eta = "N/A"

            # Update every 5 seconds
            progress = round(completed / 1024 / 1024, 1)
            total_mb = round(total / 1024 / 1024, 1)
            progress_text = f"Downloading: {progress}/{total_mb} MB"
            await status_message.edit(progress_text, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
            ))
            await asyncio.sleep(5)

        # Upload the file to Telegram with a thumbnail
        file_path = download.files[0].path
        thumbnail_path = "assist/thumbnail.jpg"
        if os.path.exists(file_path):
            last_update = [time.time()]  # Track the last update time for uploads
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
                caption="",  # Empty caption
                progress=lambda current, total: progress_bar(current, total, status_message, last_update)
            )
            await status_message.edit("")  # Clear the status message after upload
            os.remove(file_path)  # Clean up storage
            await status_message.edit("✅ File uploaded and removed from storage to free up space.")
        else:
            await status_message.edit("❌ File not found after download.")

    except Exception as e:
        await message.reply(f"❌ Failed to process download: {e}")

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_operation(client, callback_query):
    global CANCEL_DOWNLOAD
    CANCEL_DOWNLOAD[callback_query.message.chat.id] = True  # Set the cancel flag
    await callback_query.answer("Cancellation in progress...")