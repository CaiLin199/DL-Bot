# Store metadata fields and user data
METADATA_FIELDS = {
    'title': '📝 Title',
    'episode': '🎬 Episode',
    'rating': '⭐ Rating',
    'description': '📄 Description',
    'genres': '🏷️ Genres',
    'cover_url': '🖼️ Cover URL',
    'download_link': '🔗 Download Link'
}

# Store user inputs and message IDs temporarily
user_inputs = {}
user_messages = {}  # To store original message IDs
current_field = {}  # To track which field user is currently editing