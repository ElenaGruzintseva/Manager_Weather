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

        def validate_temperature(self, value):
            if value is not None and not (-100 <= value <= 60):
                raise serializers.ValidationError("Температура должна быть в диапазоне от -100 до 60.")
            return value

        def validate_pressure(self, value):
            if value is not None and not (300 <= value <= 800):
                raise serializers.ValidationError("Давление должно быть в диапазоне от 300 до 800 мм рт. ст.")
            return value


class WeatherFetchRequestSerializer(serializers.Serializer):
    latitude = serializers.FloatField(
        min_value=-90.0,
        max_value=90.0,
        help_text="Широта в десятичном формате (-90.0 до 90.0)"
    )
    longitude = serializers.FloatField(
        min_value=-180.0,
        max_value=180.0,
        help_text="Долгота в десятичном формате (-180.0 до 180.0)"
    )


class WeatherFetchLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherFetchLog
        fields = [
            'id', 'location', 'status', 'error_summary',
            'response_time_ms', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
