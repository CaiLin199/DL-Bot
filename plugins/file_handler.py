from pyrogram import Client
from pyrogram.types import Message
from .link_generator import generate_link
import os

async def copy_file_to_channel(client: Client, message: Message, channel_id: int) -> None:
    """Copy document to channel with static thumbnail and create shareable link"""
    try:
        if message and message.document:
            # Define path for static thumbnail
            thumb_path = "assist/thumbnail.jpg"
            
            # Check if thumbnail exists
            if os.path.exists(thumb_path):
                # Send document to channel with static thumbnail
                channel_message = await client.send_document(
                    chat_id=channel_id,
                    document=message.document.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    thumb=thumb_path
                )
            else:
                # Send document without thumbnail if file doesn't exist
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