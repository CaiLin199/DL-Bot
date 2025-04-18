from typing import Dict

def format_genres(genres_str: str) -> str:
    """
    Convert comma-separated genres into formatted string with emojis
    Example: "Drama, Slice of Life" -> "🎭 #Drama, ☘ #Slice_of_Life"
    """
    if not genres_str:
        return ""
        
    # Genre to emoji mapping
    GENRE_EMOJIS = {
        'action': '⚔️',
        'adventure': '🌎',
        'comedy': '😂',
        'drama': '🎭',
        'fantasy': '🔮',
        'horror': '👻',
        'mystery': '🔍',
        'romance': '💕',
        'sci-fi': '🚀',
        'slice of life': '☘',
        'sports': '⚽',
        'supernatural': '✨',
        'thriller': '🔪',
        # Add more genres and emojis as needed
    }
    
    formatted_genres = []
    genres = [g.strip() for g in genres_str.split(',')]
    
    for genre in genres:
        genre_lower = genre.lower()
        emoji = GENRE_EMOJIS.get(genre_lower, '🎬')  # Default emoji if genre not found
        # Replace spaces with underscore in hashtags
        hashtag = f"#{genre.replace(' ', '_')}"
        formatted_genres.append(f"{emoji} {hashtag}")
    
    return ', '.join(formatted_genres)

def create_post_content(metadata: Dict) -> str:
    """Create formatted post content from metadata"""
    
    # Title section
    post_content = [f"{metadata.get('title', 'No Title')}\n"]
    
    # Add genres if available
    if metadata.get('genres'):
        formatted_genres = format_genres(metadata['genres'])
        post_content.append(f"‣ Genres : {formatted_genres}")
    
    # Add rating if available
    if metadata.get('rating'):
        post_content.append(f"‣ Rating : {metadata['rating']}")
    
    # Add episodes if available
    if metadata.get('episode'):
        post_content.append(f"‣ Episodes : {metadata['episode']}")
    
    # Add an empty line before description
    post_content.append("")
    
    # Add description if available
    if metadata.get('description'):
        post_content.append(f"‣ Description : {metadata['description']}")
    
    # Join all sections with newlines
    return "\n".join(post_content)