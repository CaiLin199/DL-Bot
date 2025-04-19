from pyrogram import Client
from pyrogram.types import Message
from config import CHANNEL_ID
import logging

logger = logging.getLogger(__name__)

async def save_to_channel(client: Client, file_message: Message) -> Message:
    """Save document to channel"""
    try:
        if hasattr(file_message, 'document'):
            channel_message = await client.send_document(
                chat_id=CHANNEL_ID,
                document=file_message.document.file_id,
                caption=file_message.caption if file_message.caption else None,
                file_name=file_message.document.file_name if hasattr(file_message.document, 'file_name') else None
            )
            return channel_message
        elif hasattr(file_message, 'video'):
            channel_message = await client.send_video(
                chat_id=CHANNEL_ID,
                video=file_message.video.file_id,
                caption=file_message.caption if file_message.caption else None,
                file_name=file_message.video.file_name if hasattr(file_message.video, 'file_name') else None,
                duration=file_message.video.duration if hasattr(file_message.video, 'duration') else None,
                width=file_message.video.width if hasattr(file_message.video, 'width') else None,
                height=file_message.video.height if hasattr(file_message.video, 'height') else None
            )
            return channel_message
        else:
            logger.error("Message does not contain a document or video")
            return None
            
    except Exception as e:
        logger.error(f"Error in save_to_channel: {str(e)}")
        return None