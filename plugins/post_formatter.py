from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
from bot import Bot

# Store user inputs temporarily
user_inputs = {}

# Define the metadata fields and their callbacks
METADATA_FIELDS = {
    'title': '📝 Title',
    'episode': '🎬 Episode',
    'rating': '⭐ Rating',
    'description': '📄 Description',
    'genres': '🏷️ Genres',
    'cover_url': '🖼️ Cover URL',
    'download_link': '🔗 Download Link'
}

async def create_metadata_buttons():
    """Create inline keyboard with metadata buttons"""
    buttons = []
    for field_id, field_name in METADATA_FIELDS.items():
        buttons.append([InlineKeyboardButton(
            text=field_name,
            callback_data=f"input_{field_id}"
        )])
    
    # Add the final submit button
    buttons.append([InlineKeyboardButton(
        text="START",
        callback_data="create_post"
    )])
    
    return InlineKeyboardMarkup(buttons)

@Bot.on_message(filters.command("post") & filters.private & filters.user(OWNER_ID))
async def post_command(client: Client, message: Message):
    """Handler for /post command"""
    # Initialize empty metadata for this user
    user_inputs[message.from_user.id] = {
        'title': None,
        'episode': None,
        'rating': None,
        'description': None,
        'genres': None,
        'cover_url': None,
        'download_link': None
    }
    
    await message.reply(
        "Please select the metadata you want to add:",
        reply_markup=await create_metadata_buttons()
    )

@Bot.on_callback_query(filters.regex("^input_"))
async def handle_metadata_input(client: Client, callback: CallbackQuery):
    """Handle metadata input button clicks"""
    field = callback.data.split('_')[1]
    
    # Ask for the specific input
    await callback.message.reply(f"Please send the {METADATA_FIELDS[field]}:")
    
    # Update message to wait for input
    await callback.answer()

@Bot.on_message(filters.private & filters.user(OWNER_ID))
async def handle_metadata_value(client: Client, message: Message):
    """Handle the actual input values for metadata"""
    user_id = message.from_user.id
    
    if user_id not in user_inputs:
        return
    
    # Store the input in the appropriate field
    # Logic to determine which field is being filled
    # You'll need to track the current field being edited
    
    await message.reply(
        "Input saved! Select another field or create post:",
        reply_markup=await create_metadata_buttons()
    )

@Bot.on_callback_query(filters.regex("^create_post$"))
async def create_final_post(client: Client, callback: CallbackQuery):
    """Create the final post with collected metadata"""
    user_id = callback.from_user.id
    
    if not user_inputs.get(user_id, {}).get('download_link'):
        await callback.answer("Download link is mandatory!", show_alert=True)
        return
    
    metadata = user_inputs[user_id]
    
    # Create the post format
    post_text = f"📺 {metadata['title'] or 'No Title'}\n"
    if metadata['episode']:
        post_text += f"Episode: {metadata['episode']}\n"
    if metadata['rating']:
        post_text += f"Rating: {metadata['rating']}\n"
    if metadata['description']:
        post_text += f"Description: {metadata['description']}\n"
    if metadata['genres']:
        post_text += f"Genres: {metadata['genres']}\n"
    
    # Send the formatted post
    if metadata['cover_url']:
        await client.send_photo(
            chat_id=callback.message.chat.id,
            photo=metadata['cover_url'],
            caption=post_text
        )
    else:
        await callback.message.reply_text(post_text)
    
    # Start download using the direct_downloder
    if metadata['download_link']:
        await client.send_message(
            chat_id=callback.message.chat.id,
            text=f"/ddl {metadata['download_link']}"
        )
    
    # Clear the stored inputs
    del user_inputs[user_id]
    await callback.answer("Post created successfully!")