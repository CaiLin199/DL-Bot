from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import MAIN_CHANNEL  # Make sure to add MAIN_CHANNEL to config.py
from .post_creator import create_post_content

async def send_to_main_channel(client: Client, metadata: dict, generated_link: str) -> bool:
    """
    Send the post to main channel with the generated link as button
    
    Args:
        client: Pyrogram client instance
        metadata: Dictionary containing post metadata
        generated_link: The generated file download link
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create button with generated link
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🫦 Play Now", url=generated_link)]
        ])

        # Create post content
        post_text = create_post_content(metadata)

        # Send post to channel with or without photo
        if metadata.get('cover_url'):
            await client.send_photo(
                chat_id=MAIN_CHANNEL,
                photo=metadata['cover_url'],
                caption=post_text,
                reply_markup=reply_markup
            )
        else:
            await client.send_message(
                chat_id=MAIN_CHANNEL,
                text=post_text,
                reply_markup=reply_markup
            )
        
        return True

    except Exception as e:
        print(f"Error sending to main channel: {str(e)}")
        return False