import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from bot import Bot
from .aria2_client import aria2
from .upload_handler import handle_upload
from .progress_utils import create_progress_bar, calculate_eta

CANCEL_DOWNLOAD = {}
PROGRESS_UPDATE_DELAY = 5

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False
    last_download_update = 0

    try:
        # Start the download
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

        # Download progress monitoring
        while True:
            if CANCEL_DOWNLOAD.get(message.chat.id):
                aria2.remove([gid])
                await status_message.edit("❌ Download canceled by user.")
                return

            try:
                download = aria2.get_download(gid)
            except Exception as e:
                print(f"Error getting download: {str(e)}")
                await status_message.edit("❌ Download failed to start.")
                return

            if download.is_complete:
                await status_message.edit("✅ Download completed! Preparing to upload...")
                break
            elif download.is_removed:
                await status_message.edit("❌ Download canceled or removed.")
                return
            elif download.has_failed:
                error_msg = f"❌ Download failed.\nError: {download.error_message}"
                await status_message.edit(error_msg[:4096])
                return

            current_time = time.time()
            if current_time - last_download_update >= PROGRESS_UPDATE_DELAY:
                try:
                    completed = max(0, download.completed_length)
                    total = max(1, download.total_length)
                    progress_bar, current_mb, total_mb, speed_mb = create_progress_bar(completed, total)
                    eta = calculate_eta(completed, total, speed_mb)

                    await status_message.edit(
                        f"Downloading:\n{progress_bar} {current_mb}/{total_mb} MB\n"
                        f"Speed: {speed_mb} MB/s | ETA: {eta}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                        ])
                    )
                    last_download_update = current_time
                except Exception as e:
                    print(f"Download progress error: {str(e)}")

            time.sleep(0.1)

        # Handle file upload
        await handle_upload(
            client=client,
            message=message,
            status_message=status_message,
            file_path=download.files[0].path,
            chat_id=message.chat.id,
            CANCEL_DOWNLOAD=CANCEL_DOWNLOAD
        )

    except Exception as e:
        await message.reply(f"❌ Failed to process: {str(e)}")

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_dl(_, query):
    CANCEL_DOWNLOAD[query.message.chat.id] = True
    await query.answer("Cancelling...")