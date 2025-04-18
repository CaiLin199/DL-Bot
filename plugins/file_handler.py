from pyrogram import Client
from pyrogram.types import Message
from .link_generator import generate_link
import os

async def send_with_thumbnail(client: Client, file_path: str, chat_id: int, reply_to_message_id: int = None, caption: str = None) -> Message:
    """Send document with static thumbnail"""
    try:
        # Define path for static thumbnail
        thumb_path = "assist/thumbnail.jpg"
        
        # Common parameters for send_document
        send_params = {
            'chat_id': chat_id,
            'document': file_path,
            'caption': caption
        }
        
        # Add thumbnail if exists
        if os.path.exists(thumb_path):
            send_params['thumb'] = thumb_path
        else:
            print(f"Warning: Thumbnail not found at {thumb_path}")
            
        # Add reply_to_message_id if provided
        if reply_to_message_id:
            send_params['reply_to_message_id'] = reply_to_message_id
            
        return await client.send_document(**send_params)
        
    except Exception as e:
        print(f"Error sending document: {str(e)}")
        return None

async def copy_file_to_channel(client: Client, message: Message, channel_id: int) -> dict:
    """Copy document to channel with static thumbnail and create shareable link"""
    try:
        if message and message.document:
            # Define path for static thumbnail
            thumb_path = "assist/thumbnail.jpg"
            
            # Common parameters for send_document
            send_params = {
                'chat_id': channel_id,
                'document': message.document.file_id,
                'caption': message.caption,
                'caption_entities': message.caption_entities
            }
            
            # Add thumbnail if exists
            if os.path.exists(thumb_path):
                send_params['thumb'] = thumb_path
            else:
                print(f"Warning: Thumbnail not found at {thumb_path}")
            
            # Send document to channel
            channel_message = await client.send_document(**send_params)
            
            # Generate and return link
            if channel_message:
                link_data = await generate_link(client, channel_message, channel_id)
                return link_data
            else:
                return {"success": False, "error": "Failed to send document to channel"}
                
    except Exception as e:
        error_msg = f"Error copying file to channel: {str(e)}"
        print(error_msg)
        return {"success": False, "error": error_msg}