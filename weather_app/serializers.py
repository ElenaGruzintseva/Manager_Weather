from rest_framework import serializers
from .models import WeatherData, WeatherFetchLog


class WeatherDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherData
        fields = [
            'id', 'latitude', 'longitude', 'temperature', 'pressure', 'humidity',
            'prec_type', 'prec_strength', 'wind_speed', 'wind_direction',
            'fetched_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'fetched_at']


class WeatherFetchRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class WeatherFetchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherFetchLog
        fields = [
            'id', 'location', 'status', 'error_summary',
            'response_time_ms', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
