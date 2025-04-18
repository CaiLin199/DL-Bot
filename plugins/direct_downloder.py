import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID, CHANNEL_ID, MAIN_CHANNEL
from bot import Bot
from .aria2_client import aria2
from .progress_utils import create_progress_bar, calculate_eta
from .link_generator import generate_link
from .channel_poster import send_to_main_channel
import os

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
        download = aria2.add_uris([direct_link], {
            'continue': 'true',
            'max-connection-per-server': '16',
            'split': '16',
            'min-split-size': '1M'
        })
        gid = download.gid
        
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
            except Exception:
                await status_message.edit("❌ Download failed.")
                return None

            if download.is_complete:
                await status_message.edit("✅ Download completed! Preparing to upload...")
                
                try:
                    # Step 1: Upload to private channel first (CHANNEL_ID)
                    channel_message = await client.send_document(
                        chat_id=CHANNEL_ID,
                        document=download.files[0].path,
                        caption=None
                    )
                    
                    if channel_message:
                        # Step 2: Generate link
                        link_data = await generate_link(client, channel_message, CHANNEL_ID)
                        
                        if link_data and link_data.get("success"):
                            # Step 3: Create metadata for main channel post
                            metadata = {
                                'title': os.path.basename(download.files[0].path),
                                # Add other metadata if needed
                            }
                            
                            # Step 4: Send formatted post to main channel
                            main_channel_post = await send_to_main_channel(
                                client=client,
                                metadata=metadata,
                                generated_link=link_data["text"]
                            )
                            
                            if main_channel_post:
                                await message.reply(
                                    "✅ File uploaded and posted successfully!"
                                )
                            else:
                                await message.reply(
                                    "⚠️ File uploaded but failed to post in main channel."
                                )
                        else:
                            await message.reply("⚠️ Failed to generate link.")
                            
                        # Clean up downloaded file
                        try:
                            os.remove(download.files[0].path)
                        except Exception as e:
                            print(f"Error removing file: {str(e)}")
                            
                    await status_message.delete()
                    return channel_message
                        
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