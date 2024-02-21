from django.urls import path
from . import views

app_name = 'mysocial'
urlpatterns = [
    path("", views.index, name="index"),
    path("register/", views.register, name="register" ),
    path('add_server/', views.add_server, name='add_server'),
]