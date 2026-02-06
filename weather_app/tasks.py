from celery import shared_task
from celery.utils.log import get_task_logger
from .services.data_service import WeatherDataService

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def fetch_weather_task(self, city: str):
    """Получает данные о погоде для города"""
    try:
        logger.info(f"Fetching weather for {city}")
        service = WeatherDataService()
        result = service.fetch_and_save(city)

        if result:
            logger.info(f"Success: {city}")
        else:
            logger.error(f"Failed: {city}")

        return {'city': city, 'success': result is not None}
    except Exception as exc:
        logger.error(f"Task error for {city}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
