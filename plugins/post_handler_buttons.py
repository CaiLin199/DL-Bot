from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from .post_handler_processor import PostProcessor

# Metadata fields and their display names
METADATA_FIELDS = {
    'title': '📝 Title',
    'episode': '🎬 Episode Number',
    'genres': '🏷 Genres',
    'description': '📋 Description',
    'cover': '🖼 Cover Image',
    'download_link': '⬇️ Download Link',  # This is the key that matters
    'rating': '⭐ Rating'
}

class PostHandlerButtons:
    @staticmethod
    async def update_metadata_buttons(message: Message, user_id: int):
        """Update metadata buttons with current status"""
        keyboard = []
        metadata = PostProcessor.get_user_metadata(user_id)
        
        # Create buttons for each metadata field
        for field_id, field_name in METADATA_FIELDS.items():
            status = "✅" if metadata.get(field_id) else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{field_name} {status}",
                    callback_data=f"metadata_{field_id}"  # This will now use 'download_link' instead of 'download'
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("👁 Preview Post", callback_data="preview_post")
        ])
        
        if metadata.get('download_link'):  # Make sure to use 'download_link' here too
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
        keyboard = []
        for field_id, field_name in METADATA_FIELDS.items():
            keyboard.append([
                InlineKeyboardButton(
                    f"{field_name} ❌",
                    callback_data=f"metadata_{field_id}"  # This will now use 'download_link' instead of 'download'
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
        PostProcessor.set_user_message(message.from_user.id, main_message)

# Command handler
@Bot.on_message(filters.command("post"))
async def post_command(client: Client, message: Message):
    """Handle /post command"""
    await PostHandlerButtons.show_metadata_buttons(message)

# Callback query handler
@Bot.on_callback_query(filters.regex('^metadata_|^preview_post$|^start_process$|^cancel_input$|^notify_link_required$'))
async def callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle callback queries"""
    if callback_query.data.startswith('metadata_'):
        field = callback_query.data.split('_')[1]
        await PostProcessor.handle_metadata_input(client, callback_query, METADATA_FIELDS)
    elif callback_query.data == 'preview_post':
        await PostProcessor.preview_post(callback_query, METADATA_FIELDS)
    elif callback_query.data == 'start_process':
        await PostProcessor.start_download_process(client, callback_query)
    elif callback_query.data == 'cancel_input':
        await PostProcessor.cancel_input(callback_query)
    elif callback_query.data == 'notify_link_required':
        await PostProcessor.notify_link_required(callback_query)

# Message handler for metadata input
@Bot.on_message(filters.private & filters.text)
async def handle_metadata_message(client: Client, message: Message):
    """Handle metadata input messages"""
    if not message.text.startswith('/'):
        await PostProcessor.save_metadata(client, message, PostHandlerButtons.update_metadata_buttons)