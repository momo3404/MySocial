from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

app_name = 'mysocial'
urlpatterns = [
    path("", views.index, name="index"),
    path('register/', views.register, name="register" ),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('add_server/', views.add_server, name='add_server'),
    path('node_connection/<str:node_name>', views.NodeConnection.as_view(), name='node_connection'),
    path('api/<str:node_name>/info/', views.NodeInfoAPIView.as_view(), name='node_info'),

    path('authors/', views.AuthorList.as_view(), name='authors'),
    path('authors/<uuid:authorId>/', views.AuthorView.as_view(), name='authors-detail'),
    path('authors/<uuid:authorId>/followers/', views.FollowerList.as_view()),
    path('authors/<uuid:authorId>/followers/<uuid:follower>/', views.FollowDetail.as_view()),
    
    path('profile/<uuid:author_id>/', views.public_profile, name='public_profile'),

    path('authors/<uuid:authorId>/posts/', views.PostListCreateView.as_view(), name='posts_by_author'),
    path('profile/<uuid:author_id>/edit_display_name/', views.edit_display_name, name='edit_display_name'),
    path('profile/<uuid:author_id>/follow/', views.follow, name='follow'),
    path('profile/<uuid:author_id>/unfollow/', views.unfollow, name='unfollow'),
    
    path('follow_requests/<uuid:author_id>/', views.follow_requests, name='follow_requests'),

    path('github-activity/', views.fetch_github_activity, name='github-activity'),
]

