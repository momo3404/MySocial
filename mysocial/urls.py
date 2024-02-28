from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

app_name = 'mysocial'
urlpatterns = [
    path("", views.index, name="index"),
    path('register/', views.register, name="register" ),
    path('login/', LoginView.as_view(template_name='base/registration/login.html'), name='login'),
    path('add_server/', views.add_server, name='add_server'),
    path('node_connection/<str:node_name>', views.NodeConnection.as_view(), name='node_connection'),
    path('api/<str:node_name>/info/', views.NodeInfoAPIView.as_view(), name='node_info'),

    path('authors/', views.AuthorList.as_view(), name='authors'),
    path('authors/<uuid:authorId>/', views.AuthorView.as_view(), name='authors-detail'),
    path('authors/<uuid:authorId>/followers/', views.FollowerList.as_view()),
    path('authors/<uuid:authorId>/followers/<uuid:follower>/', views.FollowDetail.as_view()),
    
    path('profile/<uuid:author_id>/', views.public_profile, name='public_profile'),
]

