#useless codes
'''from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging
from config import OWNER_ID
from bot import Bot

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CHANNELS = ["@HeavenlySubs"]
STICKER = "CAACAgUAAxkBAAIJZGfLOdpxPmkKJ_nlJICh0bmi7GF1AALLFwACWARYVg4ubUgM9uuVNgQ"  # replace with your sticker file ID

# Temporary storage for user input
user_data = {}

async def reset_user_data(user_id):
    if user_id in user_data:
        user_data.pop(user_id)
    logger.debug(f"User data reset for {user_id}")

@Bot.on_message(filters.command("post") & filters.private & filters.user(OWNER_ID))
async def post_handler(client, message: Message):
    user_id = message.from_user.id
    command_parts = message.text.split()

    if len(command_parts) < 2 or not command_parts[1].isdigit():
        await message.reply("Usage: `/post <episode_number>`\nExample: `/post 12`")
        return

    episode_number = int(command_parts[1])
    if not (1 <= episode_number <= 500):
        await message.reply("Episode number must be between 1 and 500.")
        return

    user_data[user_id] = {
        "episode": episode_number,
        "in_progress": True
    }

    await message.reply("Send the button URL (starting with http:// or https://).")
    logger.debug(f"Episode number {episode_number} saved for {user_id}")

@Bot.on_message(filters.text & filters.private & filters.user(OWNER_ID))
async def url_handler(client, message: Message):
    user_id = message.from_user.id
    user_input = message.text.strip()

    if user_id not in user_data or "episode" not in user_data[user_id]:
        return  

    if not user_input.startswith("http://") and not user_input.startswith("https://"):
        await message.reply("Invalid URL. Please provide a valid link (starting with http:// or https://).")
        return

    user_data[user_id]["button_url"] = user_input
    episode_number = user_data[user_id]["episode"]
    anime_cover_path = "assist/cover.jpg"  # Use local image

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ / ᴡᴀᴛᴄʜ •", url=user_input)],
         [InlineKeyboardButton("✅ Send to Channels", callback_data=f"send|{user_id}")]]
    )

    post_text = (
        f"**☗   Battle Through The Heavens**\n\n"
        f"**⦿   Ratings: 9.8**\n"
        f"**⦿   Status: Airing**\n"
        f"**⦿   Episode: {episode_number}**\n"
        f"**⦿   Quality: 720p**\n"
        f"**⦿   Genres: `Action`, `Adventure`, `Harem`, `Romance`, `Cultivation`**\n\n"
        f"**◆   Synopsis: __In a land where no magic is present. A land where the strong make the rules and weak have to obey...[Read More](https://myanimelist.net/anime/36491/Doupo_Cangqiong)__**\n"
    )

    await message.reply_photo(
        photo=anime_cover_path,  
        caption=post_text,
        reply_markup=button,
        parse_mode=ParseMode.MARKDOWN
    )

    logger.debug(f"Preview sent to {user_id}, waiting for confirmation")

@Bot.on_callback_query(filters.regex(r"^send\|(\d+)$"))
async def send_to_channels(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))

    if user_id not in user_data or "episode" not in user_data[user_id] or "button_url" not in user_data[user_id]:
        await callback_query.answer("Invalid request.", show_alert=True)
        return

    episode_number = user_data[user_id]["episode"]
    anime_cover_path = "assist/cover.jpg"
    button_url = user_data[user_id]["button_url"]

    button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ / ᴡᴀᴛᴄʜ •", url=button_url)]]
    )

    post_text = (
        f"**☗   Battle Through The Heavens**\n\n"
        f"**⦿   Ratings: 9.8**\n"
        f"**⦿   Status: Airing**\n"
        f"**⦿   Episode: {episode_number}**\n"
        f"**⦿   Quality: 720p**\n"
        f"**⦿   Genres: `Action`, `Adventure`, `Harem`, `Romance`, `Cultivation`**\n\n"
        f"**◆   Synopsis: __In a land where no magic is present. A land where the strong make the rules and weak have to obey...[Read More](https://myanimelist.net/anime/36491/Doupo_Cangqiong)__**\n"
    )

    for channel in CHANNELS:
        try:
            await client.send_photo(
                chat_id=channel,
                photo=anime_cover_path,
                caption=post_text,
                reply_markup=button,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Post sent to {channel}")
        except Exception as e:
            logger.error(f"Failed to post to {channel}: {e}")

    await callback_query.answer("Post sent to channels!", show_alert=True)
    
    # Send a sticker to the channels
    for channel in CHANNELS:
        try:
            await client.send_sticker(chat_id=channel, sticker=STICKER)
            logger.info(f"Sticker sent to {channel}")
        except Exception as e:
            logger.error(f"Failed to send sticker to {channel}: {e}")
    
    await reset_user_data(user_id)
'''