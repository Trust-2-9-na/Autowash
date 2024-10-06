from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, SystemSettings, SystemStatus, SensorData
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.forms import AuthenticationForm
import re
# Signup form for new users

class SignupForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username is already taken.')
        return username

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')

        # Password must be at least 8 characters long
        if len(password1) < 8:
            raise ValidationError('Password must be at least 8 characters long.')

        # Password must contain at least one digit
        if not any(char.isdigit() for char in password1):
            raise ValidationError('Password must contain at least one digit.')

        # Password must contain at least one uppercase letter
        if not any(char.isupper() for char in password1):
            raise ValidationError('Password must contain at least one uppercase letter.')

        # Password must contain at least one lowercase letter
        if not any(char.islower() for char in password1):
            raise ValidationError('Password must contain at least one lowercase letter.')

        # Password must contain at least one special character
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password1):
            raise ValidationError('Password must contain at least one special character.')

        return password1

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Check if the passwords match
        if password1 and password2 and password1 != password2:
            raise ValidationError('Passwords do not match.')

        return cleaned_data

# Form for user profile management
class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(label='First Name')
    last_name = forms.CharField(label='Last Name')
    email = forms.EmailField(label='Email')

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'address', 'phone_number', 'profile_picture']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'address-line1'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'tel'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

 
class SystemStatusForm(forms.ModelForm):
    class Meta:
        model = SystemStatus
        fields = ['water_level', 'ultrasonic_distance_cm', 'operational_state', 'anomaly_detected', 'anomaly_description']  # Corrected fields
        labels = {
            'water_level': 'Water Level (cm)',  
            'ultrasonic_distance_cm': 'Ultrasonic Distance (cm)',  
            'operational_state': 'Operational State',
            'anomaly_detected': 'Anomaly Detected',
            'anomaly_description': 'Anomaly Description',
        }
        widgets = {
            'water_level': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'ultrasonic_distance_cm': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'operational_state': forms.Select(attrs={'class': 'form-control'}),
            'anomaly_detected': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'anomaly_description': forms.Textarea(attrs={'class': 'form-control'}),
        }


class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if not username or not password:
            raise forms.ValidationError('Please enter both username and password.')

        return super().clean()

