from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_USERNAME
import base64
import logging

logger = logging.getLogger(__name__)

async def encode_file_id(message_id: int, channel_id: int) -> str:
    """Encode message and channel IDs"""
    try:
        string = f"get-{message_id * abs(channel_id)}"
        string_bytes = string.encode('ascii')
        base64_bytes = base64.b64encode(string_bytes)
        base64_string = base64_bytes.decode('ascii')
        return base64_string
    except Exception as e:
        logger.error(f"Encoding error: {str(e)}")
        return None

async def generate_link(client: Client, channel_message: Message) -> dict:
    """Generate shareable link for channel message"""
    try:
        if not channel_message or not channel_message.id:
            logger.error("Invalid channel message provided")
            return {
                "success": False,
                "error": "Invalid channel message"
            }
            
        # Generate base64 string
        base64_string = await encode_file_id(channel_message.id, channel_message.chat.id)
        
        if base64_string:
            # Create the link with bot username
            link = f"https://t.me/{BOT_USERNAME}?start={base64_string}"
            
            # Create share button
            reply_markup = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "🔁 Share URL",
                    url=f'https://telegram.me/share/url?url={link}'
                )
            ]])
            
            # Get file details for the message
            file_details = ""
            if hasattr(channel_message, 'document'):
                file_size = channel_message.document.file_size
                file_name = getattr(channel_message.document, 'file_name', 'Document')
                file_details = f"\n\n📁 File: {file_name}\n📦 Size: {format_size(file_size)}"
            elif hasattr(channel_message, 'video'):
                file_size = channel_message.video.file_size
                file_name = getattr(channel_message.video, 'file_name', 'Video')
                duration = getattr(channel_message.video, 'duration', 0)
                file_details = f"\n\n🎥 File: {file_name}\n⏱ Duration: {format_duration(duration)}\n📦 Size: {format_size(file_size)}"
            
            return {
                "success": True,
                "text": f"<b>Here is your link</b>{file_details}\n\n🔗 {link}",
                "reply_markup": reply_markup
            }
        else:
            logger.error("Failed to encode file ID")
            return {
                "success": False,
                "error": "Failed to generate link"
            }
            
    except Exception as e:
        logger.error(f"Link generation error: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate link: {str(e)}"
        }

def format_size(size_in_bytes):
    """Format file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} TB"

def format_duration(seconds):
    """Format duration to HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"