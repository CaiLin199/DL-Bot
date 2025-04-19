from pyrogram import Client
from pyrogram.types import Message
from config import CHANNEL_ID
from .link_generator import generate_link
import logging

logger = logging.getLogger(__name__)

async def save_to_channel(client: Client, file_message: Message) -> dict:
    """
    Save document to channel and get share link
    Returns dict with link info or None if failed
    """
    try:
        # Get document file_id
        if not file_message.document:
            logger.error("Message does not contain a document")
            return None
            
        file_id = file_message.document.file_id

        # Send to channel
        channel_message = await client.send_document(
            chat_id=CHANNEL_ID,
            document=file_id
        )

        if not channel_message:
            logger.error("Failed to send document to channel")
            return None

        # Generate share link using link_generator
        link_info = await generate_link(client, channel_message, CHANNEL_ID)
        
        if not link_info["success"]:
            logger.error("Failed to generate share link")
            return None

        return link_info

    except Exception as e:
        logger.error(f"Error in save_to_channel: {str(e)}")
        return None