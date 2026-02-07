from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import timedelta
from .pipeline.base import PipelineManager
from .pipeline.actions.fetch import FetchWeatherAction
from .pipeline.actions.store import StoreWeatherDataAction
from .pipeline.actions.log import LogWeatherFetchAction
from .pipeline.actions.notify_telegram import NotifyTelegramAction
from .models import WeatherFetchLog
import time

logger = get_task_logger('api_tasks')


def create_weather_pipeline():
    """Создать экземпляр пайплайна с действиями"""
    manager = PipelineManager()
    manager.register_action(FetchWeatherAction(config=settings.PIPELINE_CONFIG.get('fetch_weather', {})))
    manager.register_action(StoreWeatherDataAction(config=settings.PIPELINE_CONFIG.get('store_data', {})))
    manager.register_action(LogWeatherFetchAction(config=settings.PIPELINE_CONFIG.get('log_to_db', {})))
    manager.register_action(NotifyTelegramAction(config=settings.PIPELINE_CONFIG.get('notify_telegram', {})))

    return manager


@shared_task(bind=True, max_retries=3)
def fetch_weather_task(self, lat: float, lon: float):
    """Celery задача для получения и сохранения данных о погоде через пайплайн"""
    try:
        logger.info(f"Запуск пайплайна для lat={lat}, lon={lon}")
        start_time = time.time()

        initial_context = {
            'latitude': lat,
            'longitude': lon,
            'task_id': self.request.id,
        }

        pipeline_manager = create_weather_pipeline()
        result = pipeline_manager.execute(initial_context)

        duration = (time.time() - start_time) * 1000  # в миллисекундах
        result.data['fetch_duration_ms'] = duration

        success = result.data.get('storage_success', False)
        weather_id = result.data.get('stored_weather_id')

        if success:
            logger.info(f"Пайплайн завершен успешно для ({lat}, {lon}), ID: {weather_id}")
        else:
            logger.error(f"Пайплайн не удался для ({lat}, {lon})")

        return {
            'coordinates': (lat, lon),
            'success': success,
            'weather_id': weather_id,
            'duration_ms': duration
        }
    except Exception as exc:
        logger.error(f"Ошибка задачи пайплайна для ({lat}, {lon}): {str(exc)}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def fetch_weather_for_multiple_locations(locations: list):
    """
    Задача для получения данных о погоде для нескольких локаций
    locations = [{'lat': 55.75, 'lon': 37.62}, ...]
    """
    results = {}
    for location in locations:
        lat = location.get('lat')
        lon = location.get('lon')

        if lat is not None and lon is not None:
            try:
                # Отправляем каждую задачу fetch_weather_task в очередь
                task = fetch_weather_task.delay(lat, lon)
                results[f"{lat},{lon}"] = task.id
                logger.info(f"Запланирована задача для ({lat}, {lon}): {task.id}")
            except Exception as e:
                logger.error(f"Ошибка при планировании задачи для ({lat}, {lon}): {str(e)}", exc_info=True)
                results[f"{lat},{lon}"] = {'error': str(e)}
        else:
            logger.warning(f"Неверные координаты в списке: {location}")
            results[f"{location}"] = {'error': 'Invalid coordinates'}

    logger.info(f"Запланировано {len(results)} задач получения погоды")
    return results


@shared_task
def periodic_weather_update():
    """Периодическая задача для обновления данных о погоде для заданных координат."""
    # Получаем список координат из настроек
    locations = getattr(settings, 'WEATHER_UPDATE_LOCATIONS', [
        {'lat': 55.75396, 'lon': 37.620393, 'city': 'Moscow'},
    ])

    location_coords = [{'lat': loc['lat'], 'lon': loc['lon']} for loc in locations]

    logger.info(f"Запуск периодического обновления погоды для {len(location_coords)} локаций")
    result_task = fetch_weather_for_multiple_locations.delay(location_coords)

    logger.info(f"Задача периодического обновления запланирована: {result_task.id}")
    return {'task_id': result_task.id, 'locations_count': len(location_coords)}


@shared_task
def log_weather_fetch_async(location: str, status: str, error_summary: str = '', response_time_ms: float = None):
    """Асинхронная задача для записи лога в БД."""
    try:
        WeatherFetchLog.objects.create(
            location=location,
            status=status,
            error_summary=error_summary,
            response_time_ms=response_time_ms
        )
        logger.info(f"Запись лога в БД выполнена для {location}")
    except Exception as e:
        logger.error(f"Ошибка при записи лога в БД для {location}: {str(e)}")


@shared_task
def cleanup_old_weather_logs(days: int = 2):
    """Задача для очистки старых записей логов"""
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = WeatherFetchLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()

    logger.info(f"Удалено {deleted_count} старых записей логов WeatherFetchLog")
    return {'deleted_count': deleted_count}
