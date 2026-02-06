from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Any
from django.conf import settings
import logging
import requests

logger = logging.getLogger('weather_client')


class WeatherAPIClient:
    """Клиент для работы с Яндекс.Погода API"""

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or settings.WEATHER_API_KEY
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _prepare_headers(self) -> dict[str, str]:
        headers = {
            'User-Agent': 'WeatherAPI-Client/1.0',
            'Accept': 'application/json',
            'X-Yandex-Weather-Key': self.api_key
        }
        return headers

    def get_weather(self, lat: float, lon: float, lang: str = 'ru') -> Optional[dict[str, Any]]:
        """Получает данные о погоде"""
        endpoint = f"{self.base_url}/v2/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'lang': lang
        }

        try:
            logger.info(f"Получение погоды для lat={lat}, lon={lon}")
            logger.debug(f"Параметры запроса: {params}")

            response = self.session.get(
                endpoint,
                params=params,
                headers=self._prepare_headers(),
                timeout=self.timeout
            )

            logger.info(f"Статус ответа: {response.status_code}")

            if response.status_code >= 400:
                logger.error(f"Ошибка API {response.status_code}: {response.text}")
                return None

            response.raise_for_status()
            data = response.json()
            logger.debug(f"Полученные данные: {data}")

            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"Ошибка парсинга JSON: {str(e)}")
            return None

    def close(self):
        self.session.close()
