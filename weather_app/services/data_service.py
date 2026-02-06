from typing import Optional, Dict, Any, List
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from ..models import WeatherData, WeatherFetchLog
from .api_client import WeatherAPIClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class WeatherDataService:
    """Сервис для работы с данными о погоде"""

    def __init__(self):
        self.api_client = WeatherAPIClient(
            base_url=settings.WEATHER_API_BASE_URL,
            api_key=settings.WEATHER_API_KEY
        )

    def fetch_and_save(self, city: str) -> Optional[WeatherData]:
        """Получает и сохраняет данные о погоде"""
        start_time = timezone.now()

        try:
            weather_data = self.api_client.get_weather(city)
            if not weather_data:
                self._log_fetch(city, 'error', 'No data received')
                return None

            weather_obj = self._save_weather_data(city, weather_data)

            response_time = (timezone.now() - start_time).total_seconds()
            self._log_fetch(city, 'success', response_time=response_time)

            cache_key = f'weather_{city.lower()}'
            cache.set(cache_key, weather_obj.id, timeout=3600)

            return weather_obj
        except Exception as e:
            logger.error(f"Error fetching weather for {city}: {str(e)}")
            self._log_fetch(city, 'error', str(e))
            return None

    def get_latest_weather(self, city: str) -> Optional[WeatherData]:
        """Получает последние данные о погоде"""
        cache_key = f'weather_{city.lower()}'
        cached_id = cache.get(cache_key)

        if cached_id:
            try:
                return WeatherData.objects.get(id=cached_id)
            except WeatherData.DoesNotExist:
                pass

        weather = WeatherData.objects.filter(
            city_lower=city.lower()
        ).only(
            'id', 'city', 'temperature', 'pressure', 'humidity',
            'prec_type', 'prec_strength', 'wind_speed', 'wind_direction',
            'fetched_at'
        ).first()

        if weather:
            cache.set(cache_key, weather.id, timeout=3600)

        return weather

    def get_weather_history(self, city: str, days: int = 7) -> List[WeatherData]:
        """Получает историю погоды"""
        cutoff_date = timezone.now() - timedelta(days=days)
        return WeatherData.objects.filter(
            city_lower=city.lower(),
            fetched_at__gte=cutoff_date
        ).order_by('-fetched_at')

    def _save_weather_data(self, city: str, data: Dict[str, Any]) -> WeatherData:
        """Сохраняет данные о погоде"""
        fact = data.get('fact', {})

        with transaction.atomic():
            weather, created = WeatherData.objects.update_or_create(
                city_lower=city.lower(),
                defaults={
                    'city': city,
                    'temperature': fact.get('temp'),
                    'pressure': fact.get('pressure_mm'),
                    'humidity': fact.get('humidity'),
                    'prec_type': fact.get('prec_type'),
                    'prec_strength': fact.get('prec_strength'),
                    'wind_speed': fact.get('wind_speed'),
                    'wind_direction': fact.get('wind_dir'),
                    'fetched_at': timezone.now(),
                }
            )
            return weather

    def _log_fetch(self, city: str, status: str, error_message: str = '', response_time: float = None):
        """Логирует запрос к API"""
        WeatherFetchLog.objects.create(
            city=city,
            status=status,
            error_message=error_message,
            response_time=response_time
        )
