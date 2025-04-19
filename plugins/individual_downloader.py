from pyrogram import Client, filters
from pyrogram.types import Message
import os
from bot import Bot
import asyncio
from .dl_progressbar import DownloadProgressBar
from .up_progressbar import UploadProgressBar
from .aria2_client import aria2

async def download_and_upload(client: Client, message: Message):
    if len(message.command) < 2:       
        return
    
    download_url = message.command[1]
    status_msg = await message.reply_text("⏳ Starting download...")
    
    try:
        # Start download using aria2
        download = aria2.add_uris([download_url])
        gid = download.gid
        
        # Initialize progress handlers
        dl_progress = DownloadProgressBar(status_msg)
        up_progress = UploadProgressBar(status_msg)
        
        # Monitor download progress
        while True:
            try:
                # Get fresh download info
                download = aria2.get_download(gid)
                download.update()  # Force update download status
                
                # Check download status
                if download.is_complete:
                    file_path = download.files[0].path
                    await status_msg.edit_text("✅ Download completed! Starting upload...")
                    
                    try:
                        await client.send_document(
                            chat_id=message.chat.id,
                            document=file_path,
                            progress=up_progress.update,
                            caption=""
                        )
                        await status_msg.delete()
                    except Exception as e:
                        await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
                    
                    # Cleanup
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    break
                    
                elif download.has_failed:
                    error_msg = download.error_message if download.error_message else "Unknown error"
                    await status_msg.edit_text(f"❌ Download failed: {error_msg}")
                    break
                    
                else:
                    # Update progress only if we have valid data
                    completed = download.completed_length
                    total = download.total_length
                    speed = download.download_speed
                    
                    if total > 0 and completed >= 0 and speed >= 0:
                        await dl_progress.update(completed, total, speed)
                
            except Exception as e:
                continue  # Skip this update if there's an error
                
            await asyncio.sleep(1)  # Reduced sleep time for more frequent updates
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# Register command handler
@Bot.on_message(filters.command("ddl"))
async def ddl_command(client: Client, message: Message):
    await download_and_upload(client, message)

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0