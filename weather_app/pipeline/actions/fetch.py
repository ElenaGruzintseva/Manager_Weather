from ...pipeline.base import PipelineAction
from ...services.data_service import WeatherDataService
import logging

logger = logging.getLogger(__name__)


class FetchWeatherAction(PipelineAction):
    """Действие для получения данных о погоде"""

    def execute(self, context: dict) -> dict:
        lat = context.get('latitude')
        lon = context.get('longitude')

        if not lat or not lon:
            raise ValueError("Широта и долгота обязательны")

        service = WeatherDataService()
        # Получаем стандартные данные
        standardized_data = service.fetch_standardized_data(lat, lon)

        if not standardized_data:
            raise Exception(f"Не удалось получить или преобразовать данные для ({lat}, {lon})")

        context['standardized_weather_data'] = standardized_data
        context['fetch_success'] = True
        logger.info(f"Стандартизированные данные погоды получены для ({lat}, {lon})")
        return context
