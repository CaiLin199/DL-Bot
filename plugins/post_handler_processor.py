from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from .individual_downloader import download_and_upload
from .item_on_db import save_to_channel
import asyncio
import logging

logger = logging.getLogger(__name__)

class PostProcessor:
    # Static storage for user metadata and messages
    _user_metadata = {}
    _user_messages = {}

    @classmethod
    def get_user_metadata(cls, user_id: int) -> dict:
        """Get user metadata"""
        if user_id not in cls._user_metadata:
            cls._user_metadata[user_id] = {}
        return cls._user_metadata[user_id]

    @classmethod
    def set_user_message(cls, user_id: int, message: Message):
        """Set user's main message"""
        cls._user_metadata[user_id] = {}
        cls._user_messages[user_id] = message

    @staticmethod
    async def handle_metadata_input(client: Client, callback_query: CallbackQuery, metadata_fields: dict):
        """Handle metadata input callbacks"""
        try:
            user_id = callback_query.from_user.id
            field = callback_query.data.split('_', 1)[1]  # Split only once to get the field name
            
            # Handle the case where field might be 'download' instead of 'download_link'
            if field == 'download':
                field = 'download_link'
            
            # Safety check for field existence
            if field not in metadata_fields:
                await callback_query.answer(f"Invalid field: {field}", show_alert=True)
                return
            
            field_display_name = metadata_fields[field].strip()
            
            input_msg = await callback_query.message.reply_text(
                f"Please send the {field_display_name}:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_input")
                ]])
            )
            
            # Store the current field and input message
            PostProcessor._user_metadata.setdefault(user_id, {})
            PostProcessor._user_metadata[user_id]['current_field'] = field
            PostProcessor._user_metadata[user_id]['input_message'] = input_msg
            
        except Exception as e:
            await callback_query.answer(f"Error: {str(e)}", show_alert=True)

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
        
        try:
            # Save the metadata
            metadata[current_field] = message.text
            await input_message.delete()
            await message.delete()
            
            # Clear current field and input message
            metadata['current_field'] = None
            metadata['input_message'] = None
            
            # Update buttons if possible
            if user_id in PostProcessor._user_messages:
                await update_buttons_callback(PostProcessor._user_messages[user_id], user_id)
        except Exception as e:
            if user_id in PostProcessor._user_messages:
                await PostProcessor._user_messages[user_id].reply_text(f"Error saving metadata: {str(e)}")

    @staticmethod
    async def start_download_process(client: Client, callback_query: CallbackQuery):
        """Start the download and upload process"""
        user_id = callback_query.from_user.id
        metadata = PostProcessor._user_metadata.get(user_id, {})
        status_message = None
        download_message = None
        result_message = None
        
        if not metadata.get('download_link'):
            await callback_query.answer("Download link is required!", show_alert=True)
            return
        
        try:
            # Create status message
            status_message = await callback_query.message.reply_text("⏳ Starting download process...")
            
            # Prepare download message
            download_message = await callback_query.message.reply_text("🔄 Processing...")
            download_message.command = ['ddl', metadata['download_link']]
            
            # Start the download process
            result_message = await download_and_upload(client, download_message)
            
            if result_message and result_message.document:
                # Save to channel and get share link
                link_info = await save_to_channel(client, result_message)
                
                if link_info and link_info["success"]:
                    # Send message with link and share button
                    await callback_query.message.reply_text(
                        text=link_info["text"],
                        reply_markup=link_info["reply_markup"]
                    )
        
        except Exception as e:
            error_msg = await callback_query.message.reply_text(f"Error: {str(e)}")
            await asyncio.sleep(10)
            await error_msg.delete()
            
        finally:
            # Cleanup
            try:
                if user_id in PostProcessor._user_metadata:
                    del PostProcessor._user_metadata[user_id]
                if user_id in PostProcessor._user_messages:
                    await PostProcessor._user_messages[user_id].delete()
                    del PostProcessor._user_messages[user_id]
                
                if status_message:
                    await status_message.delete()
                if download_message:
                    await download_message.delete()
                if result_message:
                    await result_message.delete()
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")

    @staticmethod
    async def preview_post(callback_query: CallbackQuery, metadata_fields: dict):
        """Show preview of the post with current metadata"""
        user_id = callback_query.from_user.id
        metadata = PostProcessor._user_metadata.get(user_id, {})
        
        if not metadata:
            await callback_query.answer("No metadata available for preview!", show_alert=True)
            return
        
        try:
            preview_text = "📝 Post Preview:\n\n"
            for field, display_name in metadata_fields.items():
                if field in metadata and field not in ['current_field', 'input_message']:
                    value = metadata.get(field, "Not set")
                    preview_text += f"{display_name}: {value}\n"
            
            preview_message = await callback_query.message.reply_text(preview_text)
            await asyncio.sleep(10)
            await preview_message.delete()
            
        except Exception as e:
            await callback_query.answer(f"Error showing preview: {str(e)}", show_alert=True)

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