import requests

class BaseScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_page(self, url: str) -> str:
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return r.text
            return ""
        except:
            return ""

    def __del__(self):
        try:
            self.session.close()
        except:
            pass