from typing import Optional, Any
from django.utils import timezone
from django.db import transaction
from ..models import WeatherData
from .api_client import WeatherAPIClient
from .api_adapter import WeatherAPIAdapter
import logging
from django.conf import settings

logger = logging.getLogger('weather_app')


class WeatherDataService:
    """Сервис для работы с данными о погоде"""

    def __init__(self):
        api_client = WeatherAPIClient(
            base_url=settings.WEATHER_API_BASE_URL,
            api_key=settings.WEATHER_API_KEY
        )
        # Используем адаптер
        self.api_adapter = WeatherAPIAdapter(api_client)

    def fetch_standardized_data(self, lat: float, lon: float) -> Optional[dict[str, Any]]:
        """Получает *стандартизированные* данные о погоде из адаптера."""
        return self.api_adapter.get_standardized_weather(lat, lon)

    def save_weather_data_from_standardized(self, lat: float, lon: float, standardized_data: dict[str, Any]) -> Optional[WeatherData]:
        """Сохраняет данные о погоде из стандартизированной структуры в базу."""
        # Извлечение полей из стандартизированной структуры
        timezone_name = standardized_data.get('timezone_name')
        temperature = standardized_data.get('temperature')
        pressure = standardized_data.get('pressure')
        humidity = standardized_data.get('humidity')
        prec_type = standardized_data.get('prec_type')
        prec_strength = standardized_data.get('prec_strength')
        wind_speed = standardized_data.get('wind_speed')
        wind_direction = standardized_data.get('wind_direction')

        weather_obj_data = {
            'latitude': lat,
            'longitude': lon,
            'timezone_name': timezone_name,
            'temperature': temperature,
            'pressure': pressure,
            'humidity': humidity,
            'prec_type': prec_type,
            'prec_strength': prec_strength,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
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
            logger.info(f"{'Созданы' if created else 'Обновлены'} данные погоды для ({lat}, {lon}), TZ: {timezone_name}")
            return weather_obj
        except Exception as e:
            logger.error(f"Ошибка сохранения данных для ({lat}, {lon}): {str(e)}")
            return None

    def save_weather_data(self, lat: float, lon: float, data: dict[str, Any], timezone_name: str = None) -> Optional[WeatherData]:
        """Сохраняет данные о погоде в базу."""
        fact = data.get('fact', {})
        info = data.get('info', {})

        weather_obj_data = {
            'latitude': lat,
            'longitude': lon,
            'timezone_name': timezone_name,
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
            logger.info(f"{'Созданы' if created else 'Обновлены'} данные погоды для ({lat}, {lon}), TZ: {timezone_name}")
            return weather_obj
        except Exception as e:
            logger.error(f"Ошибка сохранения данных для ({lat}, {lon}): {str(e)}")
            return None
