from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import OWNER_ID
from bot import Bot
from .parser_utils import HentaiScraper
from .formatter import format_post

scraper = HentaiScraper()

@Bot.on_message(filters.command("post") & filters.private & filters.user(OWNER_ID))
async def post_content(_, message):
    if len(message.command) < 2:
        await message.reply("Usage: /post <url>")
        return

    status = await message.reply("🔄 Fetching data...")
    
    try:
        data = scraper.get_metadata(message.command[1])
        if not data:
            await status.edit("❌ Failed to fetch data")
            return

        buttons = [[InlineKeyboardButton("⬇️ Download", url=data['dl_link'])]] if data.get('dl_link') else None
        
        if data.get('cover'):
            try:
                await message.reply_photo(
                    photo=data['cover'],
                    caption=format_post(data),
                    reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
                )
                await status.delete()
            except:
                await status.edit(
                    format_post(data),
                    reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
                )
        else:
            await status.edit(
                format_post(data),
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
            )
    except Exception as e:
        await status.edit(f"❌ Error: {str(e)}")