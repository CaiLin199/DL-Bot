import requests
from bs4 import BeautifulSoup
import time
from typing import Dict

class EpisodeParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_page_content(self, url: str) -> str:
        """Fetch page content with retry mechanism"""
        retries = 3
        while retries > 0:
            try:
                time.sleep(1)  # Respectful delay
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text
                retries -= 1
            except Exception as e:
                print(f"Error fetching page: {e}")
                retries -= 1
        return ""

    def parse_episode_url(self, url: str) -> Dict[str, str]:
        """Parse episode information from URL"""
        content = self.get_page_content(url)
        if not content:
            return {}

        try:
            soup = BeautifulSoup(content, 'html.parser')
            info = {
                'title': '',
                'episode': '',
                'cover': '',
                'rating': '',
                'dl_url': '',
                'series': ''
            }

            # Get title and episode
            if title_elem := soup.find('h1', {'class': 'entry-title'}):
                info['title'] = title_elem.text.strip()
                # Extract episode number
                if episode_elem := soup.find('span', {'class': 'episode-number'}):
                    info['episode'] = episode_elem.text.strip()

            # Get cover image
            if cover_elem := soup.find('div', {'class': 'thumb'}):
                if img := cover_elem.find('img'):
                    info['cover'] = img.get('src', '')

            # Get rating
            if rating_elem := soup.find('div', {'class': 'rating'}):
                info['rating'] = rating_elem.text.strip()

            # Get download URL
            if dl_btn := soup.find('a', {'class': 'dl-button'}):
                info['dl_url'] = dl_btn.get('href', '')

            # Get series name
            if series_elem := soup.find('div', {'class': 'series-title'}):
                info['series'] = series_elem.text.strip()

            return info

        except Exception as e:
            print(f"Error parsing page: {e}")
            return {}

    def __del__(self):
        """Cleanup session on object destruction"""
        try:
            self.session.close()
        except:
            pass