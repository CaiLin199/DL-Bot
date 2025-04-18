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
PROGRESS_UPDATE_DELAY = 5  # Update progress every 5 seconds

def create_progress_bar(current, total):
    try:
        if total <= 0:
            return "[□□□□□□□□□□]", 0, 0
            
        current_mb = round(current / 1048576, 1)
        total_mb = round(total / 1048576, 1)
        
        percentage = min(100, max(0, int((current * 100) / total)))
        blocks = min(10, max(0, int(percentage / 10)))
        progress_bar = f"[{'■' * blocks}{'□' * (10 - blocks)}]"
        
        # Calculate speed (bytes per second)
        speed_mb = round((current / time.time()) / 1048576, 1) if time.time() > 0 else 0
        
        return progress_bar, current_mb, total_mb, speed_mb
    except:
        return "[□□□□□□□□□□]", 0, 0, 0

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
                await status_message.edit(error_msg[:4096])  # Telegram message limit
                return

            current_time = time.time()
            if current_time - last_download_update >= PROGRESS_UPDATE_DELAY:
                try:
                    completed = max(0, download.completed_length)
                    total = max(1, download.total_length)
                    progress_bar, current_mb, total_mb, speed_mb = create_progress_bar(completed, total)
                    
                    # Calculate estimated time remaining
                    if speed_mb > 0:
                        remaining_mb = total_mb - current_mb
                        eta_seconds = remaining_mb / speed_mb
                        eta = str(timedelta(seconds=int(eta_seconds)))
                    else:
                        eta = "N/A"

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

            # Quick status check interval
            time.sleep(0.1)

        # Handle file upload
        file_path = download.files[0].path
        thumbnail_path = "assist/thumbnail.jpg"
        
        if os.path.exists(file_path):
            last_upload_update = 0
            upload_start_time = time.time()
            
            try:
                # Separate upload progress handler
                async def upload_progress(current, total):
                    nonlocal last_upload_update
                    now = time.time()
                    
                    if now - last_upload_update < PROGRESS_UPDATE_DELAY:
                        return
                    
                    if CANCEL_DOWNLOAD.get(message.chat.id):
                        return False

                    try:
                        progress_bar, current_mb, total_mb, speed_mb = create_progress_bar(current, total)
                        elapsed_time = now - upload_start_time
                        if elapsed_time > 0:
                            speed_mb = round((current / elapsed_time) / 1048576, 1)
                        
                        # Calculate ETA
                        if speed_mb > 0:
                            remaining_mb = (total - current) / 1048576
                            eta_seconds = remaining_mb / speed_mb
                            eta = str(timedelta(seconds=int(eta_seconds)))
                        else:
                            eta = "N/A"

                        await status_message.edit(
                            f"Uploading:\n{progress_bar} {current_mb}/{total_mb} MB\n"
                            f"Speed: {speed_mb} MB/s | ETA: {eta}",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                            ])
                        )
                        last_upload_update = now
                    except Exception as e:
                        print(f"Upload progress error: {str(e)}")
                    return True

                # Start upload
                await client.send_document(
                    chat_id=message.chat.id,
                    document=file_path,
                    thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
                    caption="",
                    progress=upload_progress
                )
                
                os.remove(file_path)
                await status_message.edit("✅ File uploaded and removed from storage.")
            except Exception as e:
                await status_message.edit(f"❌ Upload failed: {str(e)}")
        else:
            await status_message.edit("❌ File not found after download.")

    except Exception as e:
        await message.reply(f"❌ Failed to process: {str(e)}")

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_dl(_, query):
    CANCEL_DOWNLOAD[query.message.chat.id] = True
    await query.answer("Cancelling...")