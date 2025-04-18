import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from bot import Bot
from .aria2_client import aria2
from .progress_utils import create_progress_bar, calculate_eta
from .file_handler import send_with_thumbnail
import os

CANCEL_DOWNLOAD = {}
PROGRESS_UPDATE_DELAY = 5

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return None

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False
    last_download_update = 0

    try:
        download = aria2.add_uris([direct_link], {
            'continue': 'true',
            'max-connection-per-server': '16',
            'split': '16',
            'min-split-size': '1M'
        })
        gid = download.gid
        start_time = time.time()
        
        status_message = await message.reply(
            "📥 Download started...\n",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )

        while True:
            if CANCEL_DOWNLOAD.get(message.chat.id):
                aria2.remove([gid])
                await status_message.edit("❌ Download canceled by user.")
                return None

            try:
                download = aria2.get_download(gid)
            except Exception as e:
                await status_message.edit("❌ Download failed.")
                return None

            if download.is_complete:
                await status_message.edit("✅ Download completed! Preparing to upload...")
                
                try:
                    # Use send_with_thumbnail with the correct parameters
                    uploaded_message = await send_with_thumbnail(
                        client=client,
                        file_path=download.files[0].path,
                        chat_id=message.chat.id,
                        reply_to_message_id=message.id,
                        caption=""
                    )
                    
                    if uploaded_message:
                        await status_message.delete()
                        
                        # Clean up downloaded file
                        try:
                            os.remove(download.files[0].path)
                        except Exception as e:
                            print(f"Error removing file: {str(e)}")
                            
                        return uploaded_message
                    else:
                        await status_message.edit("❌ Upload failed!")
                        return None
                        
                except Exception as upload_error:
                    print(f"Upload error: {str(upload_error)}")
                    await status_message.edit(f"❌ Upload failed: {str(upload_error)}")
                    return None
                    
            elif download.is_removed:
                await status_message.edit("❌ Download canceled.")
                return None
            elif download.has_failed:
                await status_message.edit(f"❌ Download failed.\nError: {download.error_message}")
                return None

            current_time = time.time()
            if current_time - last_download_update >= PROGRESS_UPDATE_DELAY:
                try:
                    completed = max(0, download.completed_length)
                    total = max(1, download.total_length)
                    progress_bar, current_mb, total_mb, speed_mb = create_progress_bar(completed, total)
                    eta = calculate_eta(completed, total, speed_mb)

                    progress_text = (
                        f"Downloading:\n{progress_bar}\n"
                        f"Size: {current_mb}/{total_mb} MB\n"
                        f"Speed: {speed_mb} MB/s\n"
                        f"ETA: {eta}"
                    )

                    await status_message.edit(
                        progress_text,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                        ])
                    )
                    last_download_update = current_time
                except Exception as e:
                    print(f"Progress update error: {str(e)}")

            time.sleep(0.1)

    except Exception as e:
        error_message = f"❌ Failed to process: {str(e)}"
        print(error_message)
        await message.reply(error_message)
        return None

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_dl(_, query):
    CANCEL_DOWNLOAD[query.message.chat.id] = True
    await query.answer("Cancelling...")