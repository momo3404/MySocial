from django.urls import path
from . import views

app_name = 'mysocial'
urlpatterns = [
    path("", views.index, name="index"),
]