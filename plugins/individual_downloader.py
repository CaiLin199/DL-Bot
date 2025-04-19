from pyrogram import Client, filters
from pyrogram.types import Message
import os
from bot import Bot
import asyncio
from .dl_progressbar import DownloadProgressBar
from .up_progressbar import UploadProgressBar
from .aria2_client import aria2

async def download_and_upload(client: Client, message: Message):
    # Get the direct download link from message
    if len(message.command) < 2:
        await message.reply_text("Please provide a direct download link!\nUsage: /ddl <direct_link>")
        return
    
    download_url = message.command[1]
    
    # Send initial status message
    status_msg = await message.reply_text("⏳ Starting download...")
    
    try:
        # Start download using aria2
        download = aria2.add_uris([download_url])  # Changed from add_uri to add_uris
        
        # Initialize progress handlers
        dl_progress = DownloadProgressBar(status_msg)
        up_progress = UploadProgressBar(status_msg)
        
        # Monitor download progress
        while not download.is_complete:
            await dl_progress.update(
                download.completed_length,
                download.total_length,
                download.download_speed
            )
            if download.has_failed:
                await status_msg.edit_text(f"❌ Download failed: {download.error_message}")
                return
            await asyncio.sleep(2)
        
        # Download completed
        file_path = download.files[0].path
        await status_msg.edit_text("✅ Download completed! Starting upload...")
        
        # Upload file to user
        try:
            await client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                progress=up_progress.update,
                caption=f"📁 File: {os.path.basename(file_path)}\n📊 Size: {format_size(os.path.getsize(file_path))}"
            )
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
        
        # Cleanup
        os.remove(file_path)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# Register command handler
@Client.on_message(filters.command("ddl"))
async def ddl_command(client: Client, message: Message):
    await download_and_upload(client, message)

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0