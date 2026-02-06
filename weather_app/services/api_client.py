import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """Клиент для работы с Яндекс.Погода API"""

    def __init__(self, base_url: str, api_key: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def get_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """Получает данные о погоде"""
        endpoint = f"{self.base_url}/v2/forecast"
        params = {'city': city, 'lang': 'ru'}
        headers = {'X-Yandex-API-Key': self.api_key}

        try:
            logger.info(f"Fetching weather for {city}")
            response = self.session.get(endpoint, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Success: {city} - {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {city}: {str(e)}")
            return None

    def close(self):
        """Закрывает сессию"""
        self.session.close()
