from ...services.data_service import WeatherDataService
from ...pipeline.base import PipelineAction
import logging

logger = logging.getLogger(__name__)


class StoreWeatherDataAction(PipelineAction):
    def execute(self, context: dict) -> dict:
        # Получаем *стандартизированные* данные
        standardized_data = context.get('standardized_weather_data')
        lat = context.get('latitude')
        lon = context.get('longitude')

        if not standardized_data or not lat or not lon:
            raise ValueError("Не хватает данных для сохранения")

        info = raw_data.get('info', {})
        tz_info = info.get('tzinfo', {})
        timezone_name = tz_info.get('name')

        service = WeatherDataService()
        weather_obj = service.save_weather_data_from_standardized(lat, lon, standardized_data)

        if not weather_obj:
            raise Exception(f"Не удалось сохранить данные для ({lat}, {lon})")

        context['stored_weather_id'] = weather_obj.id
        context['storage_success'] = True
        logger.info(f"Данные погоды сохранены в БД с ID {weather_obj.id}")
        return context
