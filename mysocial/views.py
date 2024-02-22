from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import RegisterForm

# Create your views here.
def index(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()
            return render(request, 'registration/pending_approval.html')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})