from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class WeatherData(models.Model):
    """Данные о погоде"""
    city = models.CharField(max_length=100, db_index=True)
    city_lower = models.CharField(max_length=100, db_index=True)  # для быстрого поиска

    # Основные параметры
    temperature = models.FloatField()
    pressure = models.IntegerField()
    humidity = models.IntegerField()

    # Осадки
    prec_type = models.IntegerField(null=True, blank=True)
    prec_strength = models.FloatField(null=True, blank=True)

    # Ветер
    wind_speed = models.FloatField()
    wind_direction = models.IntegerField(null=True, blank=True)

    # Метаданные
    fetched_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fetched_at']
        indexes = [
            models.Index(fields=['city_lower', '-fetched_at']),
            models.Index(fields=['-fetched_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['city_lower'], name='unique_city_weather')
        ]

    def save(self, *args, **kwargs):
        self.city_lower = self.city.lower()
        super().save(*args, **kwargs)


class WeatherFetchLog(models.Model):
    """Лог запросов к внешнему API"""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('timeout', 'Timeout'),
    ]

    city = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    error_message = models.TextField(blank=True)
    response_time = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
