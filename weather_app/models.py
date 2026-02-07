from django.db import models
from django.utils import timezone


class WeatherData(models.Model):
    """Данные о погоде"""
    # Координаты
    latitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, db_index=True)

    timezone_name = models.CharField(max_length=50, null=True, blank=True, db_index=True)

    # Основные параметры
    temperature = models.FloatField(null=True, blank=True)
    pressure = models.IntegerField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True)

    # Осадки
    prec_type = models.IntegerField(null=True, blank=True)
    prec_strength = models.FloatField(null=True, blank=True)

    # Ветер
    wind_speed = models.FloatField(null=True, blank=True)
    wind_direction = models.IntegerField(null=True, blank=True)

    # Метаданные
    fetched_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fetched_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude', '-fetched_at']),
            models.Index(fields=['-fetched_at']),
            models.Index(fields=['timezone_name']),
        ]

    def __str__(self):
        tz_display = self.timezone_name or f"({self.latitude}, {self.longitude})"
        return f"{tz_display} - {self.temperature}°C"


class WeatherFetchLog(models.Model):
    """Лог запросов к внешнему API"""
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('error', 'Ошибка'),
        ('timeout', 'Таймаут'),
    ]

    location = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    error_summary = models.TextField(blank=True)
    response_time_ms = models.FloatField(null=True)  # Время ответа в мс
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.location} - {self.status} at {self.created_at}"
