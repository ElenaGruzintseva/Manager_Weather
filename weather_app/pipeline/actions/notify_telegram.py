import logging
import requests
from ...pipeline.base import PipelineAction

logger = logging.getLogger(__name__)


class TelegramNotificationService:
    """Сервис для отправки уведомлений в Telegram."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, chat_id: str, message: str) -> bool:
        """Отправить сообщение в чат."""
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            if response.status_code == 200 and response.json().get('ok'):
                logger.info(f"Сообщение отправлено в чат {chat_id}")
                return True
            else:
                logger.error(f"Ошибка при отправке в чат {chat_id}: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка подключения при отправке в чат {chat_id}: {str(e)}")
            return False


class NotifyTelegramAction(PipelineAction):
    """Действие для отправки уведомления о погоде в Telegram."""

    def execute(self, context: dict) -> dict:
        if not self.config.get('enabled', False):
            logger.debug("Уведомления в Telegram отключены в конфигурации")
            return context

        bot_token = self.config.get('bot_token')
        chat_ids = self.config.get('chat_ids', [])

        if not bot_token or not chat_ids:
            logger.warning("Не задан токен бота или список chat_id для Telegram уведомлений")
            return context

        # Подготовка сообщения
        weather_obj_id = context.get('stored_weather_id')
        if not weather_obj_id:
            logger.warning("Нет ID сохраненных данных о погоде для уведомления")
            return context

        try:
            from ...models import WeatherData
            weather_obj = WeatherData.objects.get(id=weather_obj_id)
            message = self._format_message(weather_obj)
        except WeatherData.DoesNotExist:
            logger.error(f"Данные о погоде с ID {weather_obj_id} не найдены для уведомления")
            return context

        # Отправка сообщений
        service = TelegramNotificationService(bot_token)
        successful_sends = 0
        for chat_id in chat_ids:
            chat_id = chat_id.strip()
            if service.send_message(chat_id, message):
                successful_sends += 1

        logger.info(f"Уведомления в Telegram отправлены: {successful_sends}/{len(chat_ids)}")
        context['telegram_notification_sent'] = True
        return context

    def _format_message(self, weather_data) -> str:
        """Форматирует сообщение для Telegram."""
        # Пример формата сообщения
        location_desc = weather_data.timezone_name or f"({weather_data.latitude}, {weather_data.longitude})"

        return (
            f"<b>Погода в {location_desc}</b>\n"
            f"Температура: {weather_data.temperature}°C\n"
            f"Давление: {weather_data.pressure} мм рт. ст.\n"
            f"Влажность: {weather_data.humidity}%\n"
        )
