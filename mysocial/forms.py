from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import RemoteServer

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        
        
class RemoteServerForm(forms.ModelForm):
    class Meta:
        model = RemoteServer
        fields = ['url', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }