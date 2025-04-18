from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .post_metadata import METADATA_FIELDS, user_inputs, user_messages, current_field

async def create_metadata_buttons(user_id):
    """Create inline keyboard with metadata buttons"""
    buttons = []
    for field_id, field_name in METADATA_FIELDS.items():
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