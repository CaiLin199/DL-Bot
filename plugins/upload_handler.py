import os
import time
import asyncio
from bot import Bot
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

PROGRESS_BAR_LENGTH = 25
PROGRESS_UPDATE_DELAY = 5

async def progress_callback(current, total, status_message: Message):
    if not hasattr(progress_callback, 'last_update_time'):
        progress_callback.last_update_time = 0

    current_time = time.time()
    if current_time - progress_callback.last_update_time < PROGRESS_UPDATE_DELAY:
        return

    try:
        progress = current / total
        filled_length = int(PROGRESS_BAR_LENGTH * progress)
        unfilled_length = PROGRESS_BAR_LENGTH - filled_length

        progress_bar = '█' * filled_length + '░' * unfilled_length
        current_mb = f"{current / 1024 / 1024:.2f}"
        total_mb = f"{total / 1024 / 1024:.2f}"
        speed = current / (current_time - progress_callback.start_time) if hasattr(progress_callback, 'start_time') else 0
        speed_mb = f"{speed / 1024 / 1024:.2f}"
        eta = (total - current) / speed if speed > 0 else 0
        eta_formatted = time.strftime('%H:%M:%S', time.gmtime(eta))

        await status_message.edit(
            f"Uploading:\n{progress_bar} {current_mb}/{total_mb} MB\n"
            f"Speed: {speed_mb} MB/s | ETA: {eta_formatted}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )
        progress_callback.last_update_time = current_time

    except Exception as e:
        print(f"Progress callback error: {str(e)}")

async def handle_upload(client: Client, message: Message, status_message: Message, file_path: str, chat_id: int, CANCEL_DOWNLOAD: dict):
    try:
        if not os.path.exists(file_path):
            await status_message.edit("❌ File not found for upload.")
            return None

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            await status_message.edit("❌ File is empty.")
            return None

        await status_message.edit(
            "📤 Starting upload...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
        )

        # Set start time for speed calculation
        progress_callback.start_time = time.time()
        progress_callback.last_update_time = 0

        try:
            # Upload the file and store the response
            uploaded_message = await client.send_document(
                chat_id=chat_id,
                document=file_path,
                progress=progress_callback,
                progress_args=(status_message,)
            )

            # Clean up
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file: {str(e)}")

            await status_message.delete()
            
            # Return the uploaded message
            return uploaded_message

        except asyncio.CancelledError:
            await status_message.edit("❌ Upload cancelled.")
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file after cancel: {str(e)}")
            return None

        except Exception as upload_error:
            await status_message.edit(f"❌ Upload failed: {str(upload_error)}")
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error removing file after upload error: {str(e)}")
            return None

    except Exception as e:
        await status_message.edit(f"❌ Upload preparation failed: {str(e)}")
        return None