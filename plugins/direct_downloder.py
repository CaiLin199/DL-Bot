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
        if total <= 0:  # Check if total is zero or negative
            return "[□□□□□□□□□□]"
        
        # Ensure current is not negative and doesn't exceed total
        current = max(0, min(current, total))
        
        # Calculate percentage with safe division
        percentage = int((current * 100) / total)
        
        # Ensure blocks calculation is safe
        blocks = min(10, max(0, int(percentage / 10)))
        completed_blocks = "■" * blocks
        remaining_blocks = "□" * (10 - blocks)
        
        return f"[{completed_blocks}{remaining_blocks}]"
    except:
        return "[□□□□□□□□□□]"

async def progress_bar(current, total, status_message, last_update):
    try:
        if CANCEL_DOWNLOAD.get(status_message.chat.id):
            await status_message.edit("❌ Upload canceled by user.")
            return False

        current_time = time.time()
        if current_time - last_update[0] >= 5:  # 5-second delay between updates
            try:
                # Ensure values are valid
                current = max(0, current)
                total = max(1, total)  # Ensure total is never zero
                
                # Calculate sizes in MB with safe division
                current_mb = round(current / 1048576, 1)
                total_mb = round(total / 1048576, 1)
                
                # Create progress bar
                pbar = create_progress_bar(current, total)
                
                # Create progress text
                progress_text = f"Uploading: {pbar} {current_mb} Mʙ | {total_mb} Mʙ"
                
                await status_message.edit(
                    progress_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                    ])
                )
                last_update[0] = current_time
            except Exception as e:
                print(f"Progress update error: {str(e)}")
        return True
    except Exception as e:
        print(f"Progress bar error: {str(e)}")
        return True

@Bot.on_message(filters.command("ddl") & filters.private & filters.user(OWNER_ID))
async def direct_downloader(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]
    CANCEL_DOWNLOAD[message.chat.id] = False

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

        last_update = [0]  # For tracking last progress update time
        while True:
            try:
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
                    try:
                        completed = max(0, download.completed_length)
                        total = max(1, download.total_length)  # Ensure total is never zero
                        
                        # Create download progress bar
                        pbar = create_progress_bar(completed, total)
                        current_mb = round(completed / 1048576, 1)
                        total_mb = round(total / 1048576, 1)
                        
                        progress_text = f"Downloading: {pbar} {current_mb} Mʙ | {total_mb} Mʙ"
                        await status_message.edit(
                            progress_text,
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
                            ])
                        )
                        last_update[0] = current_time
                    except Exception as e:
                        print(f"Progress update error: {str(e)}")
                
                time.sleep(1)  # Small delay to prevent CPU overuse
            except Exception as e:
                print(f"Download progress error: {str(e)}")
                time.sleep(1)
                continue

        # Upload the file to Telegram with a thumbnail
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
            await status_message.edit("")  # Clear the status message after upload
            os.remove(file_path)  # Clean up storage
            await status_message.edit("✅ File uploaded and removed from storage.")
        else:
            await status_message.edit("❌ File not found after download.")

    except Exception as e:
        await message.reply(f"❌ Failed to process download: {e}")

@Bot.on_callback_query(filters.regex("cancel"))
async def cancel_operation(client, callback_query):
    CANCEL_DOWNLOAD[callback_query.message.chat.id] = True
    await callback_query.answer("Cancellation in progress...")