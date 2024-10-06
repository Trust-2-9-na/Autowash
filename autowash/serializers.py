
from rest_framework import serializers
from .models import SensorData, SystemSettings, SystemStatus, UserProfile

from django.conf import settings

class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['dispensing_time', 'speed_value']

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = [
            'timestamp',
            'hands_washed',
            'water_dispensed_ml',
            'current_water_volume_ml',
            'ir_sensor_detected',
            'last_known_volume_ml'
        ]

class SystemStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemStatus
        fields = '__all__'
        
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
