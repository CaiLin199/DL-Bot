import time
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, CHANNEL_ID, MAIN_CHANNEL
from bot import Bot
from .aria2_client import aria2
from .progress_utils import create_progress_bar, calculate_eta
from .link_generator import generate_link
from .channel_poster import send_to_main_channel
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
    last_download_update = 0

    try:
        # Download started message
        status_message = await message.reply(
            "📥 Download started...\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )

        try:
            download = aria2.add_uris([direct_link], {
                'continue': 'true',
                'max-connection-per-server': '16',
                'split': '16',
                'min-split-size': '1M'
            })
            gid = download.gid
        except Exception as aria_error:
            await status_message.edit(f"❌ Download initialization failed: {str(aria_error)}")
            return None

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
                await status_message.edit("✅ Download completed! Processing file...")
                file_path = download.files[0].path
                break
            elif download.has_failed:
                await status_message.edit(f"❌ Download failed.\nError: {download.error_message}")
                return None
            elif download.is_removed:
                await status_message.edit("❌ Download canceled.")
                return None

            current_time = time.time()
            if current_time - last_download_update >= PROGRESS_UPDATE_DELAY:
                try:
                    completed = max(0, download.completed_length)
                    total = max(1, download.total_length)
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
                    last_download_update = current_time
                except Exception as e:
                    print(f"Progress update error: {str(e)}")

            await asyncio.sleep(PROGRESS_UPDATE_DELAY)

        try:
            # Step 1: Upload to bot PM with thumbnail
            await status_message.edit("📤 Uploading with thumbnail...")
            pm_message = await send_with_thumbnail(
                client=client,
                file_path=file_path,
                chat_id=message.chat.id,
                reply_to_message_id=message.id
            )

            if not pm_message:
                await status_message.edit("❌ Failed to upload with thumbnail!")
                return None

            # Step 2: Copy to CHANNEL_ID
            link_data = await copy_file_to_channel(client, pm_message, CHANNEL_ID)
            
            if not link_data.get("success"):
                await status_message.edit(f"❌ Failed to copy to channel: {link_data.get('error')}")
                return None

            await status_message.edit("✅ File uploaded successfully!")
            return pm_message

        except Exception as process_error:
            await status_message.edit(f"❌ Process failed: {str(process_error)}")
            return None
        finally:
            # Clean up
            try:
                if os.path.exists(file_path):
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