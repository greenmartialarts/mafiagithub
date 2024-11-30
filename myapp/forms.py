from django import forms
from .models import Room, Player, BugReport
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RoomCreationForm(forms.ModelForm):
    password = forms.CharField(
        max_length=128, 
        required=False,
        widget=forms.PasswordInput(),
        help_text="Optional: Set a password to make this room private"
    )

    class Meta:
        model = Room
        fields = ['room_name', 'password']

class JoinRoomForm(forms.Form):
    room_code = forms.CharField(max_length=6, min_length=6)
    password = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.PasswordInput()
    )

class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['name']

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

class BugReportForm(forms.ModelForm):
    class Meta:
        model = BugReport
        fields = ['title', 'description', 'steps_to_reproduce', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'steps_to_reproduce': forms.Textarea(attrs={'rows': 4}),
        }