#!/usr/bin/env python
"""Запуск задачи получения погоды"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_api_project.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from weather_app.tasks import fetch_weather_task, fetch_weather_for_multiple_locations
from django.conf import settings

print("=== Запуск задачи получения погоды ===\n")

# Вариант 1: Один город
print("1️⃣  Запуск задачи для Москвы...")
result = fetch_weather_task.delay(55.75396, 37.620393, 'Moscow')
print(f"   Task ID: {result.id}")
print(f"   Статус: {result.status}\n")

# Вариант 2: Несколько городов
print("2️⃣  Запуск задач для нескольких городов...")
locations = [
    {'lat': 55.75396, 'lon': 37.620393, 'city': 'Moscow'},
    {'lat': 59.93428, 'lon': 30.335099, 'city': 'St.Petersburg'},
    {'lat': 55.008354, 'lon': 82.93573, 'city': 'Novosibirsk'},
]
result = fetch_weather_for_multiple_locations.delay(locations)
print(f"   Task ID: {result.id}")
print(f"   Статус: {result.status}\n")

print("✅ Задачи запущены! Проверяйте логи.")
print("\nДля просмотра результата:")
print("  - Откройте логи: tail -f logs/celery.log")
print("  - Или проверьте базу данных через админку Django")
