def format_post(data: dict) -> str:
    text = f"📺 {data.get('title', 'N/A')}\n\n"
    
    fields = {
        'ep_num': ('Episode', ''),
        'rating': ('Rating', '⭐'),
        'quality': ('Quality', '🎥'),
        'size': ('Size', '💾')
    }
    
    for key, (label, emoji) in fields.items():
        if key in data:
            text += f"{label}: {emoji} {data[key]}\n"
    
    if 'genres' in data and data['genres']:
        text += f"\nGenres: 🏷 {', '.join(data['genres'])}\n"
    
    if 'studios' in data and data['studios']:
        text += f"\nStudios: 🎬 {', '.join(data['studios'])}\n"
    
    return text