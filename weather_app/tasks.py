from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import timedelta
from .pipeline.base import PipelineManager
from .pipeline.actions.fetch import FetchWeatherAction
from .pipeline.actions.store import StoreWeatherDataAction
from .pipeline.actions.log import LogWeatherFetchAction
from .models import WeatherFetchLog
import time

logger = get_task_logger('api_tasks')


def create_weather_pipeline():
    """Создать экземпляр пайплайна с действиями"""
    manager = PipelineManager()
    manager.register_action(FetchWeatherAction(config={'enabled': True}))
    manager.register_action(StoreWeatherDataAction(config={'enabled': True}))
    manager.register_action(LogWeatherFetchAction(config={'enabled': True}))
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
def cleanup_old_weather_logs(days: int = 3):
    """Задача для очистки старых записей логов"""
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted_count, _ = WeatherFetchLog.objects.filter(
        created_at__lt=cutoff_date
    ).delete()

    logger.info(f"Удалено {deleted_count} старых записей логов WeatherFetchLog")
    return {'deleted_count': deleted_count}
