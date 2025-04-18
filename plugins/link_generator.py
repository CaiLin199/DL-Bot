from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import base64

async def encode(string):
    """Encode a string to base64"""
    try:
        string_bytes = string.encode('ascii')
        base64_bytes = base64.b64encode(string_bytes)
        base64_string = base64_bytes.decode('ascii')
        return base64_string
    except Exception as e:
        print(f"Encoding error: {str(e)}")
        return None

async def generate_link(client: Client, channel_message: Message, channel_id: int) -> dict:
    """Generate shareable link for channel message"""
    try:
        if channel_message and channel_message.id:
            # Generate base64 string
            base64_string = await encode(f"get-{channel_message.id * abs(channel_id)}")
            
            if base64_string:
                # Create the link
                link = f"https://t.me/HeavenlySubsBot?start={base64_string}"
                
                # Create share button
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
                ])
                
                return {
                    "success": True,
                    "text": f"<b>Here is your link</b>\n\n{link}",
                    "reply_markup": reply_markup
                }
    except Exception as e:
        print(f"Link generation error: {str(e)}")
    
    return {
        "success": False,
        "error": "Failed to generate link"
    }