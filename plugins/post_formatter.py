from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
from bot import Bot

# Store user inputs and message IDs temporarily
user_inputs = {}
user_messages = {}  # To store original message IDs
current_field = {}  # To track which field user is currently editing

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

async def create_metadata_buttons(user_id):
    """Create inline keyboard with metadata buttons"""
    buttons = []
    for field_id, field_name in METADATA_FIELDS.items():
        # Add a checkmark if field has been filled
        display_name = f"✅ {field_name}" if user_inputs.get(user_id, {}).get(field_id) else field_name
        buttons.append([InlineKeyboardButton(
            text=display_name,
            callback_data=f"input_{field_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="START",
        callback_data="create_post"
    )])
    
    return InlineKeyboardMarkup(buttons)

def reset_user_data(user_id):
    """Reset all user data"""
    if user_id in user_inputs:
        del user_inputs[user_id]
    if user_id in user_messages:
        del user_messages[user_id]
    if user_id in current_field:
        del current_field[user_id]

@Bot.on_message(filters.command("post") & filters.private & filters.user(OWNER_ID))
async def post_command(client: Client, message: Message):
    """Handler for /post command"""
    user_id = message.from_user.id
    
    # Reset all data for this user
    reset_user_data(user_id)
    
    # Initialize empty metadata for this user
    user_inputs[user_id] = {
        'title': None,
        'episode': None,
        'rating': None,
        'description': None,
        'genres': None,
        'cover_url': None,
        'download_link': None
    }
    
    # Send initial message with buttons and store its message ID
    msg = await message.reply(
        "Please select the metadata you want to add:",
        reply_markup=await create_metadata_buttons(user_id)
    )
    user_messages[user_id] = {
        'main_message': msg.id,
        'instruction_message': None
    }

@Bot.on_callback_query(filters.regex("^input_"))
async def handle_metadata_input(client: Client, callback: CallbackQuery):
    """Handle metadata input button clicks"""
    user_id = callback.from_user.id
    field = callback.data.split('_')[1]
    
    # Store which field is being edited
    current_field[user_id] = field
    
    # Send instruction message and store its ID
    instruction_msg = await callback.message.reply(
        f"Please send the {METADATA_FIELDS[field]}:" +
        ("\n\nCurrent value: " + user_inputs[user_id][field] if user_inputs[user_id][field] else "")
    )
    
    # Store instruction message ID for later deletion
    user_messages[user_id]['instruction_message'] = instruction_msg.id
    
    await callback.answer()

@Bot.on_message(filters.private & filters.user(OWNER_ID))
async def handle_metadata_value(client: Client, message: Message):
    """Handle the actual input values for metadata"""
    user_id = message.from_user.id
    
    # Ignore if not in input mode or if it's a command
    if user_id not in current_field or message.text.startswith('/'):
        return
    
    field = current_field[user_id]
    
    # Save the input
    user_inputs[user_id][field] = message.text
    
    # Delete the instruction message
    if user_messages[user_id]['instruction_message']:
        try:
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=user_messages[user_id]['instruction_message']
            )
        except:
            pass
    
    # Update the main message with updated buttons
    try:
        await client.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=user_messages[user_id]['main_message'],
            reply_markup=await create_metadata_buttons(user_id)
        )
    except:
        pass
    
    # Clear current field
    current_field[user_id] = None
    
    # Delete user's input message
    try:
        await message.delete()
    except:
        pass

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
    
    # Clear all stored data for this user
    reset_user_data(user_id)
    await callback.answer("Post created successfully!")