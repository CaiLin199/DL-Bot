import time
from datetime import timedelta

def create_progress_bar(current, total):
    try:
        if total <= 0:
            return "[□□□□□□□□□□]", 0, 0, 0
            
        current_mb = round(current / 1048576, 1)
        total_mb = round(total / 1048576, 1)
        
        percentage = min(100, max(0, int((current * 100) / total)))
        blocks = min(10, max(0, int(percentage / 10)))
        progress_bar = f"[{'■' * blocks}{'□' * (10 - blocks)}]"
        
        # Calculate speed (bytes per second)
        speed_mb = round((current / time.time()) / 1048576, 1) if time.time() > 0 else 0
        
        return progress_bar, current_mb, total_mb, speed_mb
    except:
        return "[□□□□□□□□□□]", 0, 0, 0

def calculate_eta(current, total, speed_mb):
    try:
        if speed_mb > 0:
            remaining_mb = (total - current) / 1048576
            eta_seconds = remaining_mb / speed_mb
            return str(timedelta(seconds=int(eta_seconds)))
        return "N/A"
    except:
        return "N/A"