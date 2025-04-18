from pyrogram import Client
from pyrogram.types import Message

async def copy_file_to_channel(client: Client, message: Message, channel_id: int) -> None:
    """Copy document to channel without forward tag"""
    try:
        if message and message.document:
            await client.send_document(
                chat_id=channel_id,
                document=message.document.file_id,
                caption=message.caption,
                caption_entities=message.caption_entities
            )
    except Exception as e:
        print(f"Error copying file to channel: {str(e)}")