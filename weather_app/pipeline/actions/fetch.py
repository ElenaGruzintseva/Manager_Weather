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
        raw_data = service.fetch_raw_data(lat, lon)

        if not raw_data:
            raise Exception(f"Не удалось получить данные для ({lat}, {lon})")

        context['raw_weather_data'] = raw_data
        context['fetch_success'] = True
        logger.info(f"Данные погоды получены для ({lat}, {lon})")
        return context
