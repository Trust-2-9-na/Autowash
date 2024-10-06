from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .forms import UserProfileForm, SystemStatusForm, SignupForm
from .models import SystemSettings, SystemStatus, SensorData, UserProfile
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.views import LoginView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import SensorData, SystemSettings
from .serializers import SensorDataSerializer, SystemSettingsSerializer
from rest_framework import viewsets
from .models import SensorData, SystemSettings, SystemStatus, UserProfile
from .serializers import SensorDataSerializer, SystemSettingsSerializer, SystemStatusSerializer, UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging
from django.utils import timezone
import json
from django.db.models import Avg, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging
from .models import SensorData, SystemSettings, SystemStatus, UserProfile
from .serializers import SensorDataSerializer, SystemSettingsSerializer, SystemStatusSerializer, UserProfileSerializer
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view
from requests.exceptions import RequestException
from django.conf import settings
from .forms import CustomAuthenticationForm
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
class UnifiedAPIView(APIView):
    http_method_names = ['get', 'post']

    def get(self, request, *args, **kwargs):
        # Retrieve and serialize all sensor data and system status
        sensor_data = SensorData.objects.all()
        system_status = SystemStatus.objects.all()

        sensor_data_serializer = SensorDataSerializer(sensor_data, many=True)
        system_status_serializer = SystemStatusSerializer(system_status, many=True)

        combined_data = {
            'sensor_data': sensor_data_serializer.data,
            'system_status': system_status_serializer.data,
        }

        return Response(combined_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Handle sensor data and system status in POST request
        sensor_data = request.data.get('sensor_data')
        system_status = request.data.get('system_status')

        if sensor_data:
            sensor_data_serializer = SensorDataSerializer(data=sensor_data)
            if sensor_data_serializer.is_valid():
                sensor_data_serializer.save()
            else:
                return Response(sensor_data_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if system_status:
            system_status_serializer = SystemStatusSerializer(data=system_status)
            if system_status_serializer.is_valid():
                system_status_serializer.save()
            else:
                return Response(system_status_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Data saved successfully'}, status=status.HTTP_201_CREATED)


DISPENSING_TIMES = [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000]
SPEED_VALUES = [0, 64, 85, 100, 120, 128, 160, 190, 220, 240, 255]
@csrf_exempt
def system_settings_control(request):
    if request.method == "GET":
        # Fetch and return the current system settings
        settings = SystemSettings.objects.first()
        if settings is None:
            return JsonResponse({"error": "No system settings found."}, status=404)

        # Serialize the current settings
        system_settings_serializer = SystemSettingsSerializer(settings)
        return JsonResponse(system_settings_serializer.data, status=200)

    elif request.method == "POST":
        # Update the system settings based on the client's request
        try:
            data = json.loads(request.body)

            settings = SystemSettings.objects.first()
            if settings is None:
                return JsonResponse({"error": "No system settings found."}, status=404)

            # Extract the new settings from the request
            dispensing_time_index = data.get("dispensing_time_index")
            speed_value_index = data.get("speed_value_index")

            # Validate the indices
            if dispensing_time_index is not None and speed_value_index is not None:
                # Validate indices against the predefined dispensing times and speed values
                if (0 <= dispensing_time_index < len(DISPENSING_TIMES)) and (0 <= speed_value_index < len(SPEED_VALUES)):
                    # Update the system settings with valid indices
                    settings.dispensing_time = dispensing_time_index
                    settings.speed_value = speed_value_index
                    settings.save()

                    # Return the updated settings
                    return JsonResponse({
                        "dispensing_time_index": settings.dispensing_time,
                        "speed_value_index": settings.speed_value,
                        "dispensing_time": DISPENSING_TIMES[dispensing_time_index],
                        "speed_value": SPEED_VALUES[speed_value_index]
                    }, status=200)
                else:
                    return JsonResponse({"error": "Invalid index for dispensing time or speed."}, status=400)
            else:
                return JsonResponse({"error": "Missing required parameters."}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Bad request"}, status=400)



class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer

class SystemSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = SystemSettingsSerializer

    def get_queryset(self):
        user = self.request.user
        return SystemSettings.objects.filter(user=user)

    def get_object(self):
        user = self.request.user
        return SystemSettings.objects.get(user=user)

class SystemStatusViewSet(viewsets.ModelViewSet):
    queryset = SystemStatus.objects.all()
    serializer_class = SystemStatusSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class SensorDataList(APIView):
    def get(self, request, *args, **kwargs):
        sensor_data = SensorData.objects.all()
        serializer = SensorDataSerializer(sensor_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = SensorDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
 
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SystemStatusList(APIView):
    def get(self, request, *args, **kwargs):
        status_data = SystemStatus.objects.all()
        serializer = SystemStatusSerializer(status_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = SystemStatusSerializer(data=request.data)
        if serializer.is_valid():
            # Check if an entry for the user already exists and update it if it does
            user = request.user
            if SystemStatus.objects.filter(user=user).exists():
                system_status = SystemStatus.objects.get(user=user)
                serializer = SystemStatusSerializer(system_status, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Create a new entry if it does not exist
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileList(APIView):
    def get(self, request, *args, **kwargs):
        profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        data['user'] = user.id  # Ensure the user field is set
        serializer = UserProfileSerializer(data=data)
        if serializer.is_valid():
            # Check if a profile for the user already exists and update it if it does
            if UserProfile.objects.filter(user=user).exists():
                profile = UserProfile.objects.get(user=user)
                serializer = UserProfileSerializer(profile, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Create a new profile if it does not exist
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(LoginView):
    template_name = 'autowash/login.html'
    redirect_authenticated_user = True 
    form_class = CustomAuthenticationForm

def calculate_hourly_averages():
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # Query data from the past hour
    recent_data = SensorData.objects.filter(timestamp__range=(one_hour_ago, now))
    
    if recent_data.exists():
        avg_hands_washed = recent_data.aggregate(Avg('hands_washed'))['hands_washed__avg']
        avg_water_dispensed = recent_data.aggregate(Avg('water_dispensed_ml'))['water_dispensed_ml__avg']
        
        # Round to two decimal places
        avg_hands_washed = round(avg_hands_washed, 1) if avg_hands_washed is not None else 0
        avg_water_dispensed = round(avg_water_dispensed, 1) if avg_water_dispensed is not None else 0
    else:
        avg_hands_washed = 0
        avg_water_dispensed = 0

    return avg_hands_washed, avg_water_dispensed


# Updated view function that includes both daily totals and hourly averages
def average_sensor_view(request):
    # Calculate hourly averages
    avg_hands_washed, avg_water_dispensed = calculate_hourly_averages()
    
    # Calculate daily totals (last 24 hours)
    now = timezone.now()
    last_24_hours = now - timedelta(hours=24)
    
    sensor_data_last_24h = SensorData.objects.filter(timestamp__gte=last_24_hours)
    
    total_hands_washed = sensor_data_last_24h.aggregate(Sum('hands_washed'))['hands_washed__sum'] or 0
    total_water_dispensed_ml = sensor_data_last_24h.aggregate(Sum('water_dispensed_ml'))['water_dispensed_ml__sum'] or 0.0
    total_water_dispensed_liters = total_water_dispensed_ml / 1000.0  # Convert ml to liters

    # Pass both hourly averages and daily totals into the context
    context = {
        'avg_hands_washed': avg_hands_washed,
        'avg_water_dispensed': avg_water_dispensed,
        'total_hands_washed': total_hands_washed,
        'total_water_dispensed_ml': total_water_dispensed_ml,
        'total_water_dispensed_liters': total_water_dispensed_liters,
    }
    
    return render(request, 'average_sensor.html', context)

@login_required
def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if not name or not email or not message:
            messages.error(request, "All fields are required.")
            return redirect('contact')
        
        try:
            send_mail(
                f"New Contact Message from {name}",
                message,
                email,
                ['tnachokwe@gmail.com'],  
            )
            messages.success(request, "Your message has been sent successfully.")
        except Exception as e:
            messages.error(request, "Failed to send your message. Please check your network connection and try again.")
        
        return redirect('contact')
    
    return render(request, 'contact.html')
@login_required
def index(request):
    return render(request, 'index.html')
@login_required
def about(request):
    return render(request, 'about.html')
@login_required
def help(request):
    return render(request, 'help.html')

@login_required
def sensor_charts(request):
    sensor_data = SensorData.objects.all()
    system_settings = SystemSettings.objects.all()
    sensor_data_serializer = SensorDataSerializer(sensor_data, many=True)
    system_settings_serializer = SystemSettingsSerializer(system_settings, many=True)
    sensor_data_json = json.dumps(sensor_data_serializer.data)
    system_settings_json = json.dumps(system_settings_serializer.data)

    context = {
        'sensor_data_json': sensor_data_json,
        'system_settings_json': system_settings_json,
    }
    return render(request, 'sensor_charts.html', context)

from django.http import JsonResponse
import requests

@login_required
def system_settings_view(request):
    # Get the first SystemSettings instance or create one if it doesn't exist
    settings_instance, created = SystemSettings.objects.get_or_create(pk=1)

    if request.method == 'GET':
        # Serialize the settings instance
        serializer = SystemSettingsSerializer(settings_instance)
        
        # Prepare context data for rendering
        context = {
            'settings': serializer.data,
            'dispensing_times': [{'ms': ms, 'sec': ms // 1000} for ms in settings.DISPENSING_TIMES],
            'speed_values': settings.SPEED_VALUES,
            'selected_speed_value': settings_instance.speed_value,
        }
        return render(request, 'system_settings.html', context)

    elif request.method == 'POST':
        # Deserialize and validate the POST data
        dispensing_time_index = int(request.POST.get('dispensing_time_index', 0))
        speed_value_index = int(request.POST.get('speed_value_index', 0))
        
        # Map indices to actual values
        dispensing_time = settings.DISPENSING_TIMES[dispensing_time_index]
        speed_value = settings.SPEED_VALUES[speed_value_index]
        
        data = {
            'dispensing_time': dispensing_time,
            'speed_value': speed_value
        }
        
        serializer = SystemSettingsSerializer(settings_instance, data=data)

        if serializer.is_valid():
            # Save the updated settings instance
            serializer.save()
            # Add a success message
            messages.success(request, 'Settings updated successfully!')
            # Redirect back to the settings view after a successful update
            return redirect('system-settings')
        else:
            # If validation fails, re-render the form with errors
            context = {
                'settings': serializer.data,
                'dispensing_times': [{'ms': ms, 'sec': ms // 1000} for ms in settings.DISPENSING_TIMES],
                'speed_values': settings.SPEED_VALUES,
                'selected_speed_value': settings_instance.speed_value,
                'errors': serializer.errors,
            }
            return render(request, 'system_settings.html', context)

    # Return a 405 response for any other HTTP methods
    return JsonResponse({"detail": "Invalid method."}, status=405)

@login_required
def sensor_data(request):
    sensor_data = SensorData.objects.all()
    return render(request, 'sensor_data.html', {'sensor_data': sensor_data})
    

logger = logging.getLogger(__name__)
@login_required
def system_status(request):
    try:
        system_status = SystemStatus.objects.latest('id')
        logger.debug(f"Fetched System Status: {system_status}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            data = {
                'water_level': system_status.water_level,
                'ultrasonic_distance_cm': system_status.ultrasonic_distance_cm,
                'operational_state': 'Normal',
                'anomaly_detected': system_status.anomaly_detected,
                'anomaly_description': system_status.anomaly_description,
            }
            return JsonResponse(data)

        return render(request, 'system_status.html', {'system_status': system_status})

    except SystemStatus.DoesNotExist:
        messages.error(request, 'No system status available.')
        return render(request, 'system_status.html', {'system_status': None})

@login_required
def user_profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('view-profile')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'user_profile.html', {'form': form})

@login_required
def view_profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    return render(request, 'view_profile.html', {'user_profile': user_profile})


@login_required
def view_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'view_profile.html', {'user_profile': user_profile})

def landing_page(request):
    if request.session.get('visited_website'):
        welcome_back_message = "Welcome back!"
        request.session['visited_website'] = False
    else:
        welcome_back_message = None
    
    return render(request, 'landing.html', {'welcome_back_message': welcome_back_message})
@login_required
def signout(request):
    if request.method == 'POST':
        logout(request)
        request.session['visited_website'] = True
        return redirect('login')
    else:
        return redirect('landing')                

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
        else:
            # You may want to display these errors on your form
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()

    return render(request, 'signup.html', {'form': form})

@login_required
def change_account(request):
    if request.method == 'POST':
        return redirect('home')  
    return render(request, 'change_account.html')

def stay_logged_out(request):
    return render(request,'landing.html')
            
def about_land(request):
    return render(request, 'about_land.html')
def help_land(request):
    return render(request, 'help_land.html')

def contact_land(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if not name or not email or not message:
            messages.error(request, "All fields are required.")
            return redirect('contact')
        
        try:
            send_mail(
                f"New Contact Message from {name}",
                message,
                email,
                ['tnachokwe@gmail.com'],  
            )
            messages.success(request, "Your message has been sent successfully.")
        except Exception as e:
            messages.error(request, "Failed to send your message. Please check your network connection and try again.")
        
        return redirect('contact')
    
    return render(request, 'contact_land.html')

