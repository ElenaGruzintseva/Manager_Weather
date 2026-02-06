from rest_framework import serializers
from .models import WeatherData, WeatherFetchLog


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = [
            'id', 'city', 'temperature', 'pressure', 'humidity',
            'prec_type', 'prec_strength', 'wind_speed', 'wind_direction',
            'fetched_at'
        ]


class WeatherRequestSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=100)
    force_update = serializers.BooleanField(default=False)


class BatchWeatherRequestSerializer(serializers.Serializer):
    cities = serializers.ListField(
        child=serializers.CharField(max_length=100),
        min_length=1,
        max_length=50
    )
