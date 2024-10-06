from PIL import Image
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, default='Unknown')
    last_name = models.CharField(max_length=100, default='Unknown')
    email = models.EmailField(default='unknown')
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    def __str__(self):
        if self.user:
            return self.user.username
        else:
            return "No associated user"

    @property
    def username(self):
        return self.user.username

class SensorData(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    hands_washed = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    water_dispensed_ml = models.FloatField(default=0.0)
    current_water_volume_ml = models.FloatField()
    ir_sensor_detected = models.BooleanField(default=False)
    last_known_volume_ml = models.FloatField(default=0.0)  # New field to track the last known volume

    def __str__(self):
        return (f"{self.timestamp} - Hands: {self.hands_washed}, Water Dispensed: {self.water_dispensed_ml}ml, "
                f"Current Water Volume: {self.current_water_volume_ml}ml, IR Detected: {self.ir_sensor_detected}")
@receiver(post_save, sender=SensorData)
def update_water_dispensed(sender, instance, **kwargs):
    try:
        # Get the previous reading
        previous_reading = SensorData.objects.filter(timestamp__lt=instance.timestamp).order_by('-timestamp').first()

        if previous_reading:
            # Calculate the water dispensed only if the volume decreases
            if previous_reading.current_water_volume_ml > instance.current_water_volume_ml:
                water_dispensed = previous_reading.current_water_volume_ml - instance.current_water_volume_ml
                if instance.hands_washed > 0:
                    instance.ir_sensor_detected = True
                else:
                    instance.ir_sensor_detected = False

                # Avoid saving if values are unchanged
                if instance.water_dispensed_ml != water_dispensed or instance.last_known_volume_ml != instance.current_water_volume_ml:
                    instance.water_dispensed_ml = water_dispensed
                    instance.last_known_volume_ml = instance.current_water_volume_ml
                    instance.save(update_fields=['water_dispensed_ml', 'last_known_volume_ml'])
            else:
                # If water is added, set water_dispensed_ml to 0
                if instance.water_dispensed_ml != 0.0 or instance.last_known_volume_ml != instance.current_water_volume_ml:
                    instance.water_dispensed_ml = 0.0
                    instance.last_known_volume_ml = instance.current_water_volume_ml
                    instance.save(update_fields=['water_dispensed_ml', 'last_known_volume_ml'])
        else:
            # Handle case where there is no previous reading
            if instance.water_dispensed_ml != 0.0 or instance.last_known_volume_ml != instance.current_water_volume_ml:
                instance.water_dispensed_ml = 0.0
                instance.last_known_volume_ml = instance.current_water_volume_ml
                instance.save(update_fields=['water_dispensed_ml', 'last_known_volume_ml'])
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating water dispensed: {e}")

class SystemSettings(models.Model):
    # Fields to store the index of dispensing times and speed values
    dispensing_time = models.IntegerField(default=0)
    speed_value = models.IntegerField(default=0)

    def __str__(self):
        return f"Settings: Time Index {self.dispensing_time}, Speed Index {self.speed_value}"


class SystemStatus(models.Model):
    water_level = models.FloatField(default=0.0)
    ultrasonic_distance_cm = models.FloatField(null=True, blank=True)
    operational_state = models.CharField(
        max_length=50,
        choices=[
            ('Normal', 'Normal'),
            ('Maintenance Required', 'Maintenance Required'),
        ],
        default='Normal',  
        null=True,
        blank=True
    )
    anomaly_detected = models.BooleanField(default=False)
    anomaly_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return (f"Status - Water Level: {self.water_level}cm, "
                f"Ultrasonic Distance: {self.ultrasonic_distance_cm}cm, "
                f"Operational State: {self.operational_state}, "
                f"Anomaly: {'Yes' if self.anomaly_detected else 'No'}, "
                f"Description: {self.anomaly_description}")