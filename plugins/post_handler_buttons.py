from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from .post_metadata import PostMetadata
from .post_handler_processor import PostProcessor
import asyncio

# Dictionary to store temporary metadata for each user
user_metadata = {}
# Dictionary to store the main button message for each user
user_messages = {}

# Metadata fields and their display names
METADATA_FIELDS = {
    'title': '📝 Title',
    'episode': '🎬 Episode Number',
    'genres': '🏷 Genres',
    'description': '📋 Description',
    'cover': '🖼 Cover Image',
    'download_link': '⬇️ Download Link',
    'rating': '⭐ Rating'
}

class PostHandlerButtons:
    @staticmethod
    async def update_metadata_buttons(message: Message, user_id: int):
        """Update metadata buttons with current status"""
        keyboard = []
        metadata = user_metadata.get(user_id, {})
        
        # Create buttons for each metadata field
        for field_id, field_name in METADATA_FIELDS.items():
            status = "✅" if metadata.get(field_id) else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{field_name} {status}",
                    callback_data=f"metadata_{field_id}"
                )
            ])
        
        # Add Preview button
        keyboard.append([
            InlineKeyboardButton("👁 Preview Post", callback_data="preview_post")
        ])
        
        # Add Start button only if download link is provided
        if metadata.get('download_link'):
            keyboard.append([
                InlineKeyboardButton("🚀 START", callback_data="start_process")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("⚠️ Download Link Required to Start", callback_data="notify_link_required")
            ])

        await message.edit_text(
            "Select metadata to add:\n\nNote: Download Link is mandatory to proceed.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @staticmethod
    async def show_metadata_buttons(message: Message):
        """Show initial metadata input buttons"""
        user_id = message.from_user.id
        user_metadata[user_id] = {}
        
        keyboard = []
        for field_id, field_name in METADATA_FIELDS.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{field_name} ❌",
                    callback_data=f"metadata_{field_id}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("👁 Preview Post", callback_data="preview_post")
        ])
        
        keyboard.append([
            InlineKeyboardButton("⚠️ Download Link Required to Start", callback_data="notify_link_required")
        ])
        
        main_message = await message.reply_text(
            "Select metadata to add:\n\nNote: Download Link is mandatory to proceed.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        user_messages[user_id] = main_message

# Command and callback handlers
@Bot.on_message(filters.command("post"))
async def post_command(client: Client, message: Message):
    await PostHandlerButtons.show_metadata_buttons(message)

@Bot.on_callback_query(filters.regex('^metadata_|^preview_post$|^start_process$|^cancel_input$|^notify_link_required$'))
async def callback_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.data.startswith('metadata_'):
        await PostProcessor.handle_metadata_input(client, callback_query)
    elif callback_query.data == 'preview_post':
        await PostProcessor.preview_post(callback_query)
    elif callback_query.data == 'start_process':
        await PostProcessor.start_download_process(client, callback_query)
    elif callback_query.data == 'cancel_input':
        await PostProcessor.cancel_input(callback_query)
    elif callback_query.data == 'notify_link_required':
        await PostProcessor.notify_link_required(callback_query)

@Bot.on_message(filters.private & ~filters.command)
async def handle_metadata_message(client: Client, message: Message):
    await PostProcessor.save_metadata(client, message)