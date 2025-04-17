import os
import asyncio
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from aria2p import API, Client as Aria2Client
from bot import Bot
from config import OWNER_ID, ARIA2_SECRET, ARIA2_HOST, ARIA2_PORT

# Connect to aria2 RPC server
aria2 = API(
    Aria2Client(
        host=ARIA2_HOST,
        port=ARIA2_PORT,
        secret=ARIA2_SECRET  # Blank if no secret is set
    )
)

# Reusable progress bar function
async def update_progress_bar(status_message, completed, total, speed=None, eta=None):
    progress = int((completed / total) * 10) if total != 0 else 0
    progress_bar = f"[{'■' * progress}{'□' * (10 - progress)}]"
    speed_text = f"⚡️ Speed: {round(speed / 1024 / 1024, 2)} Mʙ/s\n" if speed else ""
    eta_text = f"⌛ ETA: {eta}\n" if eta else ""
    progress_text = (
        f"Progress: {progress_bar} {round(completed / 1024 / 1024, 1)} Mʙ | {round(total / 1024 / 1024, 1)} Mʙ\n"
        f"{speed_text}{eta_text}"
    )
    await status_message.edit(progress_text)

@Bot.on_message(filters.command("ddl") & filters.private)
async def direct_downloader(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply("You are not authorized to use this command.")
        return

    if len(message.command) < 2:
        await message.reply("Usage: /ddl <direct_link>")
        return

    direct_link = message.command[1]

    try:
        # Start the download
        download = aria2.add_uris([direct_link])
        gid = download.gid
        status_message = await message.reply(f"📥 Download started with GID: {gid}...\n")

        # Monitor the download progress
        while True:
            download = aria2.get_download(gid)
            if download.is_complete:
                await status_message.edit("✅ Download completed! Uploading to Telegram...")
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
                # If eta is an integer (seconds), convert it to a string
                if isinstance(download.eta, int):
                    eta = str(timedelta(seconds=download.eta))
                else:
                    eta = str(download.eta)  # If already a timedelta, convert to string
            else:
                eta = "N/A"

            await update_progress_bar(status_message, completed, total, speed, eta)
            await asyncio.sleep(7)  # Wait for 7 seconds before updating the progress bar

        # Upload the file to Telegram with the same progress bar
        file_path = download.files[0].path  # Get the first file path
        if os.path.exists(file_path):
            async def progress_bar(current, total):
                await update_progress_bar(status_message, current, total)

            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption="📤 File uploaded successfully!",
                progress=progress_bar
            )
            await status_message.edit("✅ File uploaded successfully!")
        else:
            await status_message.edit("❌ File not found after download.")

    except Exception as e:
        await message.reply(f"❌ Failed to process download: {e}")