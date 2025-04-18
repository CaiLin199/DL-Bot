from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
from bot import Bot
from .direct_downloder import direct_downloader
from .post_metadata import METADATA_FIELDS, user_inputs, user_messages, current_field
from .post_utils import create_metadata_buttons, reset_user_data

@Bot.on_message(filters.command("post") & filters.private & filters.user(OWNER_ID))
async def post_command(client: Client, message: Message):
    """Handler for /post command"""
    user_id = message.from_user.id
    reset_user_data(user_id)
    
    user_inputs[user_id] = {
        'title': None,
        'episode': None,
        'rating': None,
        'description': None,
        'genres': None,
        'cover_url': None,
        'download_link': None
    }
    
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
    field = callback.data[6:]
    
    if field not in METADATA_FIELDS:
        await callback.answer(f"Invalid field: {field}", show_alert=True)
        return
    
    current_field[user_id] = field
    current_value = user_inputs[user_id][field] if user_id in user_inputs and field in user_inputs[user_id] else None
    instruction_text = f"Please send the {METADATA_FIELDS[field]}:"
    if current_value:
        instruction_text += f"\n\nCurrent value: {current_value}"
    
    if user_messages[user_id].get('instruction_message'):
        try:
            await client.delete_messages(
                chat_id=callback.message.chat.id,
                message_ids=user_messages[user_id]['instruction_message']
            )
        except Exception as e:
            print(f"Error deleting previous instruction message: {e}")
    
    instruction_msg = await callback.message.reply(instruction_text)
    user_messages[user_id]['instruction_message'] = instruction_msg.id
    await callback.answer()

@Bot.on_message(filters.private & filters.user(OWNER_ID))
async def handle_metadata_value(client: Client, message: Message):
    """Handle the actual input values for metadata"""
    user_id = message.from_user.id
    
    if user_id not in current_field or message.text is None or message.text.startswith('/'):
        return
    
    field = current_field[user_id]
    user_inputs[user_id][field] = message.text
    
    if user_messages[user_id].get('instruction_message'):
        try:
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=user_messages[user_id]['instruction_message']
            )
        except Exception as e:
            print(f"Error deleting instruction message: {e}")
    
    if user_messages[user_id].get('main_message'):
        try:
            await client.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=user_messages[user_id]['main_message'],
                reply_markup=await create_metadata_buttons(user_id)
            )
        except Exception as e:
            print(f"Error updating main message: {e}")
    
    current_field[user_id] = None
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
        if metadata.get('cover_url'):
            post_msg = await client.send_photo(
                chat_id=callback.message.chat.id,
                photo=metadata['cover_url'],
                caption=post_text
            )
        else:
            post_msg = await callback.message.reply_text(post_text)
        
        if metadata.get('download_link'):
            download_message = Message(
                id=0,
                chat=callback.message.chat,
                from_user=callback.from_user,
                text=f"/ddl {metadata['download_link']}",
                command=["ddl", metadata['download_link']],
                client=client
            )
            await direct_downloader(client, download_message)
        
        reset_user_data(user_id)
        await callback.answer("Post created successfully!")
    except Exception as e:
        await callback.answer(f"Error creating post: {str(e)}", show_alert=True)