from typing import Optional, Dict, Any
from .api_client import WeatherAPIClient # Текущий клиент
import logging

logger = logging.getLogger(__name__)


class WeatherAPIAdapter:
    """
    Адаптер для взаимодействия с внешним API погоды.
    Отвечает за вызов API и преобразование ответа в внутреннюю стандартную структуру.
    """

    def __init__(self, api_client: WeatherAPIClient):
        self.client = api_client

    def get_standardized_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Получает погоду от внешнего API и возвращает в стандартной внутренней структуре.
        Возвращает None в случае ошибки парсинга или если API вернул неожиданный формат.
        """
        raw_response = self.client.get_weather(lat, lon)
        if not raw_response:
            logger.warning(f"Получен пустой ответ от API для ({lat}, {lon})")
            return None

        try:
            # --- Парсинг ответа API ---
            # Предположим, старый API возвращал: {'temperature': 25, 'location': 'City'}
            # Новый API возвращает: {'fact': {'temp': -10}, 'info': {'tzinfo': {'name': 'Europe/Moscow'}}}

            # Попытка парсинга под новую структуру
            fact = raw_response.get('fact', {})
            info = raw_response.get('info', {})
            tz_info = info.get('tzinfo', {})

            standardized_data = {
                # 'temperature' и другие поля соответствуют вашей внутренней модели
                'temperature': fact.get('temp'),
                'pressure': info.get('def_pressure_mm'),
                'humidity': fact.get('humidity'),
                'prec_type': fact.get('prec_type'),
                'prec_strength': fact.get('prec_strength'),
                'wind_speed': fact.get('wind_speed'),
                'wind_direction': fact.get('wind_angle'),
                'timezone_name': tz_info.get('name'), # <-- Извлекаем имя зоны
                'raw_source_data': raw_response, # Опционально: сохранить сырой ответ для дебага
            }

            # Проверка на наличие критичных полей (опционально)
            # if standardized_data['temperature'] is None:
            #     logger.error(f"Критическое поле 'temperature' отсутствует в ответе для ({lat}, {lon}): {raw_response}")
            #     return None

            logger.debug(f"Данные успешно преобразованы для ({lat}, {lon})")
            return standardized_data

        except (KeyError, TypeError, AttributeError) as e:
            # Любая ошибка при извлечении данных указывает на изменение структуры
            logger.error(f"Ошибка парсинга ответа API для ({lat}, {lon}). "
                         f"Структура ответа могла измениться. Ошибка: {e}. "
                         f"Ответ: {raw_response}", exc_info=True)
            # Здесь можно отправить алерт (например, через logging handler или отдельный сервис)
            # alert_service.send_alert(f"API structure changed for Yandex Weather API!")
            return None
