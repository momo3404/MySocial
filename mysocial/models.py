from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

SHORT = 30 
MEDIUM = 100
ID = 500 
URL = 1000
CONTENT = 2000

def get_current_time():
    return timezone.now()
    
class Author(models.Model):
    type = models.CharField(max_length=SHORT, null=True)
    authorId = models.UUIDField(default=uuid.uuid4, unique=True)
    author_url = models.URLField(max_length=URL, unique=True)
    url = models.URLField(max_length=URL, unique=True, null=False)
    host = models.URLField(max_length=URL, null=True)
    displayName = models.CharField(max_length=SHORT, null=True)
    github = models.URLField(max_length=URL, blank=True, null=True)
    profileImage = models.ImageField(upload_to='static/images/profile_images/', null=True, blank=True, max_length=1000)
    bio = models.TextField(null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author', null=True, blank=False) 
    
    def is_friend(self, other_user):
        following = self.following.filter(follower=other_user).exists()
        followed_by = other_user.following.filter(follower=self).exists()

        return following and followed_by

    def get_mutual_follows(self):
        # this author is following
        authors_followed = Follower.objects.filter(follower=self).values_list('author__authorId', flat=True)
        
        # following this author
        authors_following = Follower.objects.filter(author=self).values_list('follower__authorId', flat=True)
        
        mutual_follows_ids = set(authors_followed).intersection(set(authors_following))
        mutual_follows = Author.objects.filter(authorId__in=mutual_follows_ids)
        
        return mutual_follows
    
    def get_followers(self):
        # following this author
        authors_following = Follower.objects.filter(author=self).values_list('follower__authorId', flat=True)

        followers = Author.objects.filter(authorId__in=authors_following)

        return followers
    
    def get_following(self):
        # this author is following
        authors_followed = Follower.objects.filter(follower=self).values_list('author__authorId', flat=True)

        following = Author.objects.filter(authorId__in=authors_followed)

        return following

    
    def __str__(self):
        return self.displayName

class Follower(models.Model):
    author = models.ForeignKey(Author, related_name='following', on_delete=models.CASCADE)
    follower = models.ForeignKey(Author, related_name='followers', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.follower.displayName + "  is following  " + self.author.displayName

class FollowRequest(models.Model):
    type = models.CharField(max_length=SHORT, default="Follow")
    summary = models.CharField(max_length=CONTENT, null=True)
    actor = models.ForeignKey(Author, related_name='requestfollowing', on_delete=models.CASCADE)
    object = models.ForeignKey(Author, related_name='requestfollowed', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.actor.displayName + "  sent a follow request to  " + self.object.displayName
    
class Post(models.Model):
    TYPE_CHOICES = [
        ('POST', 'Post'),
        ('IMAGE', 'Image'),
        ('COMMONMARK', 'Commonmark')
    ]
    type = models.CharField(max_length=SHORT, default="post", choices=TYPE_CHOICES)
    title =  models.CharField(max_length=MEDIUM, null=True)
    postId = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    url = models.URLField(max_length=URL, unique=True, null=True)
    source = models.URLField(max_length=URL, null=True)
    origin =  models.URLField(max_length=URL, null=True)
    description = models.TextField(max_length=CONTENT, null=True, blank=True)
    content_type = models.CharField(max_length=SHORT, default="post", choices=TYPE_CHOICES, null=True)
    content = models.TextField(max_length=CONTENT, null=True, blank=True)
    image = models.ImageField(upload_to='static/images/posts_images/', null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='author', null=True, blank=True)
    count = models.IntegerField(default=0)
    likesCount = models.IntegerField(default=0)
    comments = models.URLField(max_length=URL, null=True)
    published = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    VISIBILITY_CHOICES = [
        ('PUBLIC', 'Public'),
        ('PRIVATE', 'Private'),
        ('UNLISTED', 'Unlisted'),
    ]
    visibility = models.CharField(max_length=SHORT, choices=VISIBILITY_CHOICES, default="PUBLIC", null=False)

    def __str__(self):
        return self.title

class Comment(models.Model):
    type = models.CharField(max_length=SHORT, default="comment")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='comment_author')
    comment = models.TextField(max_length=CONTENT, null=False)
    contentType = models.CharField(max_length=SHORT, null=False)
    published = models.DateTimeField(auto_now_add=True)
    commentId = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comment_post')

    def __str__(self):
        return self.author.displayName + " commented"
   
    
class Node(models.Model):
    node_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node_name = models.CharField(max_length=MEDIUM, blank=True)
    url = models.URLField(max_length=URL, default="127.0.0.1:8000/")
    authors_url = models.URLField(max_length=URL, default="127.0.0.1:8000/authors")
    username = models.CharField(max_length=MEDIUM, blank=True)
    password = models.CharField(max_length=MEDIUM, blank=True)
        
class Like(models.Model):
    context = models.URLField(default="https://www.w3.org/ns/activitystreams")
    summary = models.CharField(max_length=255)
    type = models.CharField(max_length=50, default="Like")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='likes_given')
    object_url = models.URLField()  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.displayName} likes {self.object_url}"


class Inbox(models.Model):
    inbox_id = models.UUIDField(default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='inbox_items', null=True, blank=True)
    inbox_item = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
class RemoteFollow(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='remote_follow', null=True, blank=True)
    follower_inbox = models.URLField()  
    
