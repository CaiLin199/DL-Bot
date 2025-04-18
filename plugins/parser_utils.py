from bs4 import BeautifulSoup
from .scraper_base import BaseScraper

class HentaiScraper(BaseScraper):
    def get_metadata(self, url: str) -> dict:
        content = self.get_page(url)
        if not content:
            return {}

        try:
            soup = BeautifulSoup(content, 'html.parser')
            return {
                **self._get_basic_info(soup),
                **self._get_media_info(soup),
                **self._get_content_info(soup)
            }
        except:
            return {}

    def _get_basic_info(self, soup: BeautifulSoup) -> dict:
        data = {}
        
        if title := soup.find('h1', 'entry-title'):
            data['title'] = title.text.strip()
            if 'episode' in data['title'].lower():
                ep_parts = data['title'].lower().split('episode')
                data['ep_num'] = ep_parts[-1].strip()
                data['series'] = ep_parts[0].strip()

        if thumb := soup.select_one('.thumb img[src]'):
            data['cover'] = thumb['src']

        if dl := soup.select_one('.dl-button[href]'):
            data['dl_link'] = dl['href']

        return data

    def _get_media_info(self, soup: BeautifulSoup) -> dict:
        data = {}
        
        if info := soup.find('div', 'video-info'):
            if rating := info.select_one('.rating-score'):
                data['rating'] = rating.text.strip()
            if quality := info.select_one('.quality'):
                data['quality'] = quality.text.strip()
            if size := info.select_one('.size'):
                data['size'] = size.text.strip()

        return data

    def _get_content_info(self, soup: BeautifulSoup) -> dict:
        data = {}
        
        if genres := soup.select('.genres a'):
            data['genres'] = [g.text.strip() for g in genres]
        if studios := soup.select('.studios a'):
            data['studios'] = [s.text.strip() for s in studios]

        return data