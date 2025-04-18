import os
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .progress_utils import create_progress_bar, calculate_eta

PROGRESS_UPDATE_DELAY = 5

async def handle_upload(client, message, status_message, file_path, chat_id, CANCEL_DOWNLOAD):
    if not os.path.exists(file_path):
        await status_message.edit("❌ File not found after download.")
        return False

    last_upload_update = 0
    upload_start_time = time.time()
    thumbnail_path = "assist/thumbnail.jpg"
    
    try:
        async def upload_progress(current, total):
            nonlocal last_upload_update
            now = time.time()
            
            if now - last_upload_update < PROGRESS_UPDATE_DELAY:
                return
            
            if CANCEL_DOWNLOAD.get(chat_id):
                return False

            try:
                progress_bar, current_mb, total_mb, speed_mb = create_progress_bar(current, total)
                elapsed_time = now - upload_start_time
                if elapsed_time > 0:
                    speed_mb = round((current / elapsed_time) / 1048576, 1)
                
                eta = calculate_eta(current, total, speed_mb)

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

        await client.send_document(
            chat_id=chat_id,
            document=file_path,
            thumb=thumbnail_path if os.path.exists(thumbnail_path) else None,
            caption="",
            progress=upload_progress
        )
        
        os.remove(file_path)
        await status_message.edit("✅ File uploaded and removed from storage.")
        return True
    except Exception as e:
        await status_message.edit(f"❌ Upload failed: {str(e)}")
        return False