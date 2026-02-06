from ...pipeline.base import PipelineAction
from ...services.data_service import WeatherDataService
import logging

logger = logging.getLogger(__name__)


class StoreWeatherDataAction(PipelineAction):
    """Действие для сохранения данных о погоде в базу"""

    def execute(self, context: dict) -> dict:
        raw_data = context.get('raw_weather_data')
        lat = context.get('latitude')
        lon = context.get('longitude')

        if not raw_data or not lat or not lon:
            raise ValueError("Не хватает данных для сохранения")

        service = WeatherDataService()
        weather_obj = service.save_weather_data(lat, lon, raw_data)

        if not weather_obj:
            raise Exception(f"Не удалось сохранить данные для ({lat}, {lon})")

        context['stored_weather_id'] = weather_obj.id
        context['storage_success'] = True
        logger.info(f"Данные погоды сохранены в БД с ID {weather_obj.id}")
        return context
