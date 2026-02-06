from typing import Optional, Any
from django.utils import timezone
from django.db import transaction
from ..models import WeatherData
from .api_client import WeatherAPIClient
import logging
from django.conf import settings

logger = logging.getLogger('weather_app')


class WeatherDataService:
    """Сервис для работы с данными о погоде"""

    def __init__(self):
        self.api_client = WeatherAPIClient(
            base_url=settings.WEATHER_API_BASE_URL,
            api_key=settings.WEATHER_API_KEY
        )

    def fetch_raw_data(self, lat: float, lon: float) -> Optional[dict[str, Any]]:
        """Получает сырые данные о погоде из API."""
        return self.api_client.get_weather(lat, lon)

    def save_weather_data(self, lat: float, lon: float, data: dict[str, Any]) -> Optional[WeatherData]:
        """Сохраняет данные о погоде в базу."""
        fact = data.get('fact', {})
        info = data.get('info', {})

        weather_obj_data = {
            'latitude': lat,
            'longitude': lon,
            'temperature': fact.get('temp'),
            'pressure': info.get('def_pressure_mm'),
            'humidity': fact.get('humidity'),
            'prec_type': fact.get('prec_type'),
            'prec_strength': fact.get('prec_strength'),
            'wind_speed': fact.get('wind_speed'),
            'wind_direction': fact.get('wind_angle'),
            'fetched_at': timezone.now(),
        }

        # Убираем None значения
        weather_obj_data = {k: v for k, v in weather_obj_data.items() if v is not None}

        try:
            with transaction.atomic():
                weather_obj, created = WeatherData.objects.update_or_create(
                    latitude=lat,
                    longitude=lon,
                    defaults=weather_obj_data
                )
            logger.info(f"{'Созданы' if created else 'Обновлены'} данные погоды для ({lat}, {lon})")
            return weather_obj
        except Exception as e:
            logger.error(f"Ошибка сохранения данных для ({lat}, {lon}): {str(e)}")
            return None
