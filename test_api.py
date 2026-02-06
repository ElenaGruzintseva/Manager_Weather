#!/usr/bin/env python
"""Тестовый скрипт для проверки API"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_api_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from weather_app.services.api_client import WeatherAPIClient
from django.conf import settings

# Тестовые координаты (Москва)
TEST_LAT = 55.75396
TEST_LON = 37.620393

print("=== Тестирование Яндекс.Погода API ===\n")

# Создаем клиент
client = WeatherAPIClient(
    base_url=settings.WEATHER_API_BASE_URL,
    api_key=settings.WEATHER_API_KEY
)

print(f"Базовый URL: {settings.WEATHER_API_BASE_URL}")
print(f"API Key: {settings.WEATHER_API_KEY[:10]}...")
print(f"Тестовые координаты: lat={TEST_LAT}, lon={TEST_LON}")
print("\n--- Отправка запроса ---\n")

# Отправляем запрос
response = client.get_weather(TEST_LAT, TEST_LON)

if response:
    print("✅ Успешный ответ!\n")
    print("Структура ответа:")
    import json
    print(json.dumps(response, indent=2, ensure_ascii=False))
else:
    print("❌ Ошибка при получении данных")

client.close()
