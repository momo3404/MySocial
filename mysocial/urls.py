from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

app_name = 'mysocial'
urlpatterns = [
    path("", views.index, name="index"),
    path('register/', views.register, name="register" ),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('add_server/', views.add_server, name='add_server'),

    path('authors/', views.AuthorList.as_view()),
]


