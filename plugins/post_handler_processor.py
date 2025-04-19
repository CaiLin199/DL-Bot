from pyrogram import Client
from pyrogram.types import CallbackQuery, Message
from .individual_downloader import download_and_upload
import asyncio

class PostProcessor:
    @staticmethod
    async def handle_metadata_input(client: Client, callback_query: CallbackQuery):
        """Handle metadata input callbacks"""
        user_id = callback_query.from_user.id
        field = callback_query.data.split('_')[1]
        
        input_msg = await callback_query.message.reply_text(
            f"Please send the {METADATA_FIELDS[field].lower()}:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_input")
            ]])
        )
        
        user_metadata[user_id]['current_field'] = field
        user_metadata[user_id]['input_message'] = input_msg

    @staticmethod
    async def save_metadata(client: Client, message: Message):
        """Save metadata and update buttons"""
        user_id = message.from_user.id
        if user_id not in user_metadata:
            return
            
        metadata = user_metadata[user_id]
        current_field = metadata.get('current_field')
        input_message = metadata.get('input_message')
        
        if not current_field or not input_message:
            return
        
        metadata[current_field] = message.text
        await input_message.delete()
        await message.delete()
        
        metadata['current_field'] = None
        metadata['input_message'] = None
        
        if user_id in user_messages:
            from .post_handler_buttons import PostHandlerButtons
            await PostHandlerButtons.update_metadata_buttons(user_messages[user_id], user_id)

    @staticmethod
    async def start_download_process(client: Client, callback_query: CallbackQuery):
        """Start the download and upload process"""
        user_id = callback_query.from_user.id
        metadata = user_metadata.get(user_id, {})
        
        if not metadata.get('download_link'):
            await callback_query.answer("Download link is required!")
            return
        
        # Create message object for download_and_upload function
        download_message = await callback_query.message.reply_text("Starting download process...")
        download_message.command = ['ddl', metadata['download_link']]
        
        # Use existing download_and_upload function
        await download_and_upload(client, download_message)
        
        # Save metadata after successful download
        metadata.pop('current_field', None)
        metadata.pop('input_message', None)
        post = PostMetadata(**metadata)
        await post.save()
        
        # Cleanup
        if user_id in user_metadata:
            del user_metadata[user_id]
        if user_id in user_messages:
            await user_messages[user_id].delete()
            del user_messages[user_id]

    @staticmethod
    async def preview_post(callback_query: CallbackQuery):
        """Show preview of the post with current metadata"""
        user_id = callback_query.from_user.id
        metadata = user_metadata.get(user_id, {})
        
        if not metadata:
            await callback_query.answer("No metadata available for preview!")
            return
        
        preview_text = "📝 Post Preview:\n\n"
        for field, display_name in METADATA_FIELDS.items():
            if field in metadata and field != 'current_field' and field != 'input_message':
                value = metadata.get(field, "Not set")
                preview_text += f"{display_name}: {value}\n"
        
        preview_message = await callback_query.message.reply_text(preview_text)
        await asyncio.sleep(10)
        await preview_message.delete()

    @staticmethod
    async def notify_link_required(callback_query: CallbackQuery):
        await callback_query.answer(
            "⚠️ Please provide the download link first!",
            show_alert=True
        )

    @staticmethod
    async def cancel_input(callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        if user_id in user_metadata:
            metadata = user_metadata[user_id]
            if 'input_message' in metadata:
                await metadata['input_message'].delete()
                metadata['current_field'] = None
                metadata['input_message'] = None