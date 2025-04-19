from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from .individual_downloader import download_and_upload
import asyncio

class PostProcessor:
    # Static storage
    _user_metadata = {}
    _user_messages = {}

    @classmethod
    def get_user_metadata(cls, user_id: int) -> dict:
        """Get user metadata"""
        return cls._user_metadata.get(user_id, {})

    @classmethod
    def set_user_message(cls, user_id: int, message: Message):
        """Set user's main message"""
        cls._user_metadata[user_id] = {}
        cls._user_messages[user_id] = message

    @staticmethod
    async def handle_metadata_input(client: Client, callback_query: CallbackQuery, metadata_fields: dict):
        """Handle metadata input callbacks"""
        user_id = callback_query.from_user.id
        field = callback_query.data.split('_')[1]
        
        input_msg = await callback_query.message.reply_text(
            f"Please send the {metadata_fields[field].lower()}:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_input")
            ]])
        )
        
        PostProcessor._user_metadata[user_id]['current_field'] = field
        PostProcessor._user_metadata[user_id]['input_message'] = input_msg

    @staticmethod
    async def save_metadata(client: Client, message: Message, update_buttons_callback):
        """Save metadata and update buttons"""
        user_id = message.from_user.id
        if user_id not in PostProcessor._user_metadata:
            return
            
        metadata = PostProcessor._user_metadata[user_id]
        current_field = metadata.get('current_field')
        input_message = metadata.get('input_message')
        
        if not current_field or not input_message:
            return
        
        metadata[current_field] = message.text
        await input_message.delete()
        await message.delete()
        
        metadata['current_field'] = None
        metadata['input_message'] = None
        
        if user_id in PostProcessor._user_messages:
            await update_buttons_callback(PostProcessor._user_messages[user_id], user_id)

    @staticmethod
    async def start_download_process(client: Client, callback_query: CallbackQuery):
        """Start the download and upload process"""
        user_id = callback_query.from_user.id
        metadata = PostProcessor._user_metadata.get(user_id, {})
        
        if not metadata.get('download_link'):
            await callback_query.answer("Download link is required!")
            return
        
        download_message = await callback_query.message.reply_text("Starting download process...")
        download_message.command = ['ddl', metadata['download_link']]
        
        await download_and_upload(client, download_message)
        
        # Store metadata for future use (you can implement storage later)
        stored_metadata = {
            key: value for key, value in metadata.items() 
            if key not in ['current_field', 'input_message']
        }
        
        # Cleanup
        if user_id in PostProcessor._user_metadata:
            del PostProcessor._user_metadata[user_id]
        if user_id in PostProcessor._user_messages:
            await PostProcessor._user_messages[user_id].delete()
            del PostProcessor._user_messages[user_id]

    @staticmethod
    async def preview_post(callback_query: CallbackQuery, metadata_fields: dict):
        """Show preview of the post with current metadata"""
        user_id = callback_query.from_user.id
        metadata = PostProcessor._user_metadata.get(user_id, {})
        
        if not metadata:
            await callback_query.answer("No metadata available for preview!")
            return
        
        preview_text = "📝 Post Preview:\n\n"
        for field, display_name in metadata_fields.items():
            if field in metadata and field != 'current_field' and field != 'input_message':
                value = metadata.get(field, "Not set")
                preview_text += f"{display_name}: {value}\n"
        
        preview_message = await callback_query.message.reply_text(preview_text)
        await asyncio.sleep(10)
        await preview_message.delete()

    @staticmethod
    async def notify_link_required(callback_query: CallbackQuery):
        """Notify user that download link is required"""
        await callback_query.answer(
            "⚠️ Please provide the download link first!",
            show_alert=True
        )

    @staticmethod
    async def cancel_input(callback_query: CallbackQuery):
        """Cancel current input"""
        user_id = callback_query.from_user.id
        if user_id in PostProcessor._user_metadata:
            metadata = PostProcessor._user_metadata[user_id]
            if 'input_message' in metadata:
                await metadata['input_message'].delete()
                metadata['current_field'] = None
                metadata['input_message'] = None