from pyrogram import Client
from pyrogram.types import Message
from .link_generator import generate_link

async def copy_file_to_channel(client: Client, message: Message, channel_id: int) -> None:
    """Copy document to channel and create shareable link"""
    try:
        if message and message.document:
            # Send document to channel
            channel_message = await client.send_document(
                chat_id=channel_id,
                document=message.document.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities
            )
            
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