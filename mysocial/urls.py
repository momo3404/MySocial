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
    path('authors/<uuid:authorId>/liked/', views.LikedView.as_view(), name='liked'),
    path('authors/<uuid:authorId>/followers/', views.FollowerList.as_view()),
    path('authors/<uuid:authorId>/followers/<path:foreignAuthorId>/', views.FollowDetail.as_view()),
    path('authors/<uuid:authorId>/posts/', views.PostListCreateView.as_view(), name='posts_by_author'),
    path('authors/<uuid:authorId>/posts/<uuid:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('authors/<uuid:authorId>/posts/<uuid:post_id>/likes/', views.LikesView.as_view(), name='likes_post'),
    path('authors/<uuid:authorId>/posts/<uuid:post_id>/comments/', views.CommentsView.as_view(), name='comments_post'),
    path('authors/<uuid:authorId>/inbox/', views.InboxView.as_view(), name='author_inbox'),
 
    path('profile/<uuid:author_id>/', views.public_profile, name='public_profile'),
    path('profile/<uuid:author_id>/edit_profile/', views.edit_profile, name='edit_profile'),
    path('profile/<uuid:author_id>/follow/', views.follow, name='follow'),
    path('profile/<uuid:author_id>/unfollow/', views.unfollow, name='unfollow'),
    path('profile/<uuid:author_id>/inbox/', views.inbox, name='inbox'),
    path('profile/<uuid:authorId>/posts/<uuid:post_id>/comments/', views.comments_post, name='comment_post'),
    
    path('process_follow_request/', views.process_follow_request, name='process_follow_request'),
    path('posts/<uuid:post_id>/like/', views.like_post, name='like_post'),
    path('posts/<uuid:post_id>/share/', views.share_post, name='share_post'),
    path('posts/<uuid:post_id>/delete/', views.delete_post, name='delete_post'),

    path('github-activity/', views.fetch_github_activity, name='github-activity'),
]