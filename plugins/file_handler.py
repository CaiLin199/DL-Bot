from pyrogram import Client
from pyrogram.types import Message
from .link_generator import generate_link
import os

async def send_with_thumbnail(client: Client, message: Message, file_path: str, chat_id: int) -> Message:
    """Send document with static thumbnail"""
    try:
        # Define path for static thumbnail
        thumb_path = "assist/thumbnail.jpg"
        
        # Send document with or without thumbnail
        if os.path.exists(thumb_path):
            return await client.send_document(
                chat_id=chat_id,
                document=file_path,
                thumb=thumb_path,
                caption=message.text if message.text else None
            )
        else:
            print(f"Warning: Thumbnail not found at {thumb_path}")
            return await client.send_document(
                chat_id=chat_id,
                document=file_path,
                caption=message.text if message.text else None
            )
    except Exception as e:
        print(f"Error sending document: {str(e)}")
        return None

async def copy_file_to_channel(client: Client, message: Message, channel_id: int) -> None:
    """Copy document to channel with static thumbnail and create shareable link"""
    try:
        if message and message.document:
            # Define path for static thumbnail
            thumb_path = "assist/thumbnail.jpg"
            
            # Send document to channel with or without thumbnail
            if os.path.exists(thumb_path):
                channel_message = await client.send_document(
                    chat_id=channel_id,
                    document=message.document.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    thumb=thumb_path
                )
            else:
                channel_message = await client.send_document(
                    chat_id=channel_id,
                    document=message.document.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities
                )
                print(f"Warning: Thumbnail not found at {thumb_path}")
            
            # Generate and send link
            if channel_message:
                link_data = await generate_link(client, channel_message, channel_id)
                if link_data["success"]:
                    await message.reply_text(
                        text=link_data["text"],
                        quote=True,
                        reply_markup=link_data["reply_markup"]
                    )
                else:
                    print(f"Link generation failed: {link_data.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"Error copying file to channel: {str(e)}")