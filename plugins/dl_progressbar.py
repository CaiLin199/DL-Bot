from pyrogram.types import Message
import time

class DownloadProgressBar:
    def __init__(self, status_message: Message):
        self.status_message = status_message
        self.last_update_time = 0
    
    async def update(self, current, total, speed):
        now = time.time()
        
        # Update progress every 3 seconds to avoid flood
        if now - self.last_update_time < 3:
            return
        
        self.last_update_time = now
        
        # Calculate percentage and progress bar
        percentage = current * 100 / total if total != 0 else 0
        progress_bar = self._generate_progress_bar(percentage)
        
        # Format sizes
        current_size = self._format_size(current)
        total_size = self._format_size(total)
        speed_text = self._format_size(speed) + "/s"
        
        # Update status message
        text = (
            f"⬇️ Downloading...\n"
            f"{progress_bar}\n"
            f"📊 Progress: {percentage:.1f}%\n"
            f"📦 {current_size} of {total_size}\n"
            f"🚀 Speed: {speed_text}"
        )
        
        try:
            await self.status_message.edit_text(text)
        except:
            pass
    
    def _generate_progress_bar(self, percentage: float) -> str:
        completed = int(percentage / 5)  # 20 characters for 100%
        remaining = 20 - completed
        return "▓" * completed + "░" * remaining
    
    def _format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0