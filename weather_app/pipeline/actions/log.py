from ...pipeline.base import PipelineAction
import logging

logger = logging.getLogger(__name__)


class LogWeatherFetchAction(PipelineAction):
    """Действие для асинхронного логирования запроса к API"""

    def execute(self, context: dict) -> dict:
        lat = context.get('latitude')
        lon = context.get('longitude')
        fetch_success = context.get('fetch_success', False)
        fetch_duration_ms = context.get('fetch_duration_ms')

        location_str = f"{lat},{lon}"

        if fetch_success:
            status = 'success'
            error_summary = ''
        else:
            status = 'error'
            errors = context.get('errors', [])
            error_summary = '; '.join([err.get('error', 'Unknown error') for err in errors])

        from ...tasks import log_weather_fetch_async

        log_weather_fetch_async.delay(
            location=location_str,
            status=status,
            error_summary=error_summary,
            response_time_ms=fetch_duration_ms
        )

        logger.info(f"Запланировано логирование для {location_str}, статус: {status}")
        return context
