from django.urls import path, include
from . import views
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from .views import SensorDataViewSet, SystemSettingsViewSet, SystemStatusViewSet, UserProfileViewSet
from .views import SensorDataList, SystemStatusList, UserProfileList
from .views import landing_page, UnifiedAPIView, average_sensor_view, system_settings_view, system_settings_control

router = DefaultRouter()
router.register(r'sensor-data', SensorDataViewSet, basename='sensor-data')
router.register(r'system-settings', SystemSettingsViewSet, basename='system-settings')
router.register(r'system-status', SystemStatusViewSet, basename='system-status')
router.register(r'user-profile', UserProfileViewSet, basename='user-profile')


urlpatterns = [
    path('home/', views.index, name='home'),
    path('home/', views.index, name='home'),
    path('system-settings/', system_settings_view, name='system-settings'),
    path('system-status/', views.system_status, name='system-status'),
    path('user-profile/', views.user_profile, name='user-profile'),                          
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('', landing_page, name='landing'),
    path('signout/', views.signout, name='signout'),
    path('signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('help/', views.help, name='help'),
    path('view-profile/', views.view_profile, name='view-profile'),
    path('sensor-data/', views.sensor_data, name='sensor-data'),
    path('accounts/', include('allauth.urls')), 
    path('change-account/', views.change_account, name='change-account'),
    path('average-sensor/', views.average_sensor_view, name='average-sensor'),               
    path('sensor-charts/', views.sensor_charts, name='sensor-charts'),
    path('stay-logged-out/', views.stay_logged_out, name='stay_logged_out'),
    path('contact-land/', views.contact_land, name='contact-land'),
    path('help-land/', views.help_land, name='help-land'),
    path('about-land/', views.about_land, name='about-land'),


    #api urls
    path('api/unified/', UnifiedAPIView.as_view(), name='unified-api'),
    path('api/system-settings/', system_settings_control, name='system_settings_control'), 
    path('api/', include(router.urls)),
    path('sensor-data/', SensorDataList.as_view(), name='sensor-data-list'),
    path('system-status/', SystemStatusList.as_view(), name='system-status-list'),
    path('user-profile/', UserProfileList.as_view(), name='user-profile-list'),
]