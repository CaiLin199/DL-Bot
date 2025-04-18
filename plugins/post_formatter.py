from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
from bot import Bot
from .direct_downloder import direct_downloader
from pyrogram.types import Chat, User

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

    # Get the full field name after 'input_'
    field = callback.data[6:]

    # Verify the field exists in our METADATA_FIELDS
    if field not in METADATA_FIELDS:
        await callback.answer(f"Invalid field: {field}", show_alert=True)
        return

    # Store which field is being edited
    current_field[user_id] = field

    # Send instruction message and store its ID
    current_value = user_inputs[user_id][field] if user_id in user_inputs and field in user_inputs[user_id] else None
    instruction_text = f"Please send the {METADATA_FIELDS[field]}:"
    if current_value:
        instruction_text += f"\n\nCurrent value: {current_value}"

    # Delete previous instruction message if exists
    if user_messages[user_id].get('instruction_message'):
        try:
            await client.delete_messages(
                chat_id=callback.message.chat.id,
                message_ids=user_messages[user_id]['instruction_message']
            )
        except Exception as e:
            print(f"Error deleting previous instruction message: {e}")

    instruction_msg = await callback.message.reply(instruction_text)

    # Store instruction message ID for later deletion
    user_messages[user_id]['instruction_message'] = instruction_msg.id

    await callback.answer()

@Bot.on_message(filters.private & filters.user(OWNER_ID))
async def handle_metadata_value(client: Client, message: Message):
    """Handle the actual input values for metadata"""
    user_id = message.from_user.id

    # Ignore if not in input mode or if it's a command
    if user_id not in current_field or message.text is None or message.text.startswith('/'):
        return

    field = current_field[user_id]

    # Initialize user_inputs for this user if not exists
    if user_id not in user_inputs:
        user_inputs[user_id] = {
            'title': None,
            'episode': None,
            'rating': None,
            'description': None,
            'genres': None,
            'cover_url': None,
            'download_link': None
        }

    # Save the input
    user_inputs[user_id][field] = message.text

    # Delete the instruction message
    if user_id in user_messages and user_messages[user_id].get('instruction_message'):
        try:
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=user_messages[user_id]['instruction_message']
            )
        except Exception as e:
            print(f"Error deleting instruction message: {e}")

    # Update the main message with updated buttons
    if user_id in user_messages and user_messages[user_id].get('main_message'):
        try:
            await client.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=user_messages[user_id]['main_message'],
                reply_markup=await create_metadata_buttons(user_id)
            )
        except Exception as e:
            print(f"Error updating main message: {e}")

    # Clear current field
    current_field[user_id] = None

    # Delete user's input message
    try:
        await message.delete()
    except Exception as e:
        print(f"Error deleting user message: {e}")

@Bot.on_callback_query(filters.regex("^create_post$"))
async def create_final_post(client: Client, callback: CallbackQuery):
    """Create the final post with collected metadata"""
    user_id = callback.from_user.id

    if not user_inputs.get(user_id, {}).get('download_link'):
        await callback.answer("Download link is mandatory!", show_alert=True)
        return

    metadata = user_inputs[user_id]

    # Create the post format
    post_text = f"📺 {metadata.get('title', 'No Title')}\n"
    if metadata.get('episode'):
        post_text += f"Episode: {metadata['episode']}\n"
    if metadata.get('rating'):
        post_text += f"Rating: {metadata['rating']}\n"
    if metadata.get('description'):
        post_text += f"Description: {metadata['description']}\n"
    if metadata.get('genres'):
        post_text += f"Genres: {metadata['genres']}\n"

    try:
        # Send the formatted post first
        if metadata.get('cover_url'):
            post_msg = await client.send_photo(
                chat_id=callback.message.chat.id,
                photo=metadata['cover_url'],
                caption=post_text
            )
        else:
            post_msg = await callback.message.reply_text(post_text)

        # Now start the direct download
        if metadata.get('download_link'):
            # Create a message object for direct_downloader
            download_message = Message(
                id=0,  # This will be ignored
                chat=callback.message.chat,
                from_user=callback.from_user,
                text=f"/ddl {metadata['download_link']}",
                command=["ddl", metadata['download_link']],
                client=client
            )

            # Start the download
            await direct_downloader(client, download_message)

        # Clear all stored data for this user
        reset_user_data(user_id)
        await callback.answer("Post created successfully!")
    except Exception as e:
        await callback.answer(f"Error creating post: {str(e)}", show_alert=True)