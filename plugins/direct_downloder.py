import time
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, CHANNEL_ID, MAIN_CHANNEL
from bot import Bot
from .aria2_client import aria2
from .progress_utils import create_progress_bar, calculate_eta
from .file_handler import send_with_thumbnail, copy_file_to_channel

CANCEL_DOWNLOAD = {}
PROGRESS_UPDATE_DELAY = 5
last_update_time = time.time()

async def progress(current, total, message, text):
    global last_update_time
    
    try:
        now = time.time()
        if (now - last_update_time) < PROGRESS_UPDATE_DELAY:
            return
            
        last_update_time = now
        
        if total == 0:
            total = 0.00001
            
        progress_bar, current_mb, total_mb, speed_mb = create_progress_bar(current, total)
        eta = calculate_eta(current, total, speed_mb)
        
        await message.edit(
            f"{text}\n{progress_bar}\n"
            f"Size: {current_mb}/{total_mb} MB\n"
            f"Speed: {speed_mb} MB/s | ETA: {eta}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )
    except Exception as e:
        print(f"Progress update error: {str(e)}")

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return None

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False

    try:
        # Download started message
        status_message = await message.reply(
            "📥 Download started...\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )

        try:
            # Modified aria2 options for better handling
            download = aria2.add_uris([direct_link], {
                'continue': 'true',
                'max-connection-per-server': '1',
                'split': '1',
                'min-split-size': '20M',
                'check-integrity': 'true',
                'retry-wait': '3',
                'max-tries': '5'
            })
            gid = download.gid
        except Exception as aria_error:
            await status_message.edit(f"❌ Download initialization failed: {str(aria_error)}")
            return None

        file_path = None
        while True:
            if CANCEL_DOWNLOAD.get(message.chat.id):
                aria2.remove([gid])
                await status_message.edit("❌ Download canceled by user.")
                return None

            try:
                download = aria2.get_download(gid)
            except Exception:
                await status_message.edit("❌ Download failed.")
                return None

            if download.is_complete:
                file_path = download.files[0].path
                await status_message.edit("✅ Download completed! Processing file...")
                break
            elif download.has_failed:
                await status_message.edit(f"❌ Download failed.\nError: {download.error_message}")
                return None
            elif download.is_removed:
                await status_message.edit("❌ Download canceled.")
                return None

            try:
                completed = download.completed_length
                total = download.total_length or 1
                progress_bar, current_mb, total_mb, speed_mb = create_progress_bar(completed, total)
                eta = calculate_eta(completed, total, download.download_speed)

                await status_message.edit(
                    f"📥 Downloading:\n{progress_bar}\n"
                    f"Size: {current_mb}/{total_mb} MB\n"
                    f"Speed: {speed_mb} MB/s | ETA: {eta}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                    ])
                )
            except Exception as e:
                print(f"Progress update error: {str(e)}")

            await asyncio.sleep(PROGRESS_UPDATE_DELAY)

        if not file_path or not os.path.exists(file_path):
            await status_message.edit("❌ Downloaded file not found!")
            return None

        try:
            # Send directly to channel with thumbnail
            await status_message.edit("📤 Uploading to channel...")
            channel_message = await send_with_thumbnail(
                client=client,
                file_path=file_path,
                chat_id=CHANNEL_ID,
                caption=None  # We'll format the caption later
            )

            if not channel_message:
                await status_message.edit("❌ Failed to upload to channel!")
                return None

            # Send copy to PM for preview
            await status_message.edit("📬 Sending preview...")
            pm_message = await channel_message.copy(
                chat_id=message.chat.id,
                reply_to_message_id=message.id
            )

            await status_message.edit("✅ Upload completed successfully!")
            return channel_message  # Return channel message for post formatter

        except Exception as upload_error:
            await status_message.edit(f"❌ Upload failed: {str(upload_error)}")
            return None
        finally:
            # Clean up downloaded file
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Cleanup error: {str(e)}")

    except Exception as e:
        error_message = f"❌ Failed to process: {str(e)}"
        print(error_message)
        if 'status_message' in locals():
            await status_message.edit(error_message)
        else:
            await message.reply(error_message)
        return None

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_dl(_, callback_query):
    try:
        CANCEL_DOWNLOAD[callback_query.message.chat.id] = True
        await callback_query.answer("Cancelling...", cache_time=5)
    except Exception as e:
        print(f"Cancel callback error: {str(e)}")