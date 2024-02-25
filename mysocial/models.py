from django.db import models
from django.contrib.auth.models import User
import uuid

#REMOVE THESE AFTER REFACTOR
MAX_LENGTH = 1000
SHORT_MAX_LENGTH = 200

#KEEP THESE
SHORT_LENGTH = 30 
MEDIUM_LENGTH = 100
ID_LENGTH = 500 
URL_LENGTH = 1000
CONTENT_LENGTH = 2000
    
class Author(models.Model):
    type = models.CharField(max_length=SHORT_LENGTH, null=True)
    authorId = models.UUIDField(max_length=ID_LENGTH, unique=True, null=True, blank=True)
    url = models.URLField(max_length=URL_LENGTH, unique=True, null=False)
    host = models.URLField(max_length=URL_LENGTH, null=True)
    displayName = models.CharField(max_length=SHORT_LENGTH, null=True)
    github = models.URLField(max_length=URL_LENGTH, blank=True, null=True)
    profileImage = models.URLField(max_length=URL_LENGTH, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author', null=True, blank=False) 

    def __str__(self):
        return self.displayName

class Follower(models.Model):
    attributes = models.JSONField(null=True, blank=True)
    follower = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='items', null=True, blank=True)
    
    def __str__(self):
        return self.follower.displayName + "  sent a follow request to  " + self.attributes["displayName"]

class FollowRequest(models.Model):
    type = models.CharField(max_length=SHORT_LENGTH, default="Follow")
    summary = models.CharField(max_length=CONTENT_LENGTH, null=True)
    actor = models.JSONField()
    object = models.JSONField()
    
    def __str__(self):
        return self.summary
    
class Post(models.Model):
    type = models.CharField(max_length=SHORT_LENGTH, default="post")
    title =  models.CharField(max_length=MEDIUM_LENGTH, null=True)
    postId = models.UUIDField(max_length=ID_LENGTH, unique=True, null=True, blank=True)
    url = models.URLField(max_length=URL_LENGTH, unique=True, null=True)
    source = models.URLField(max_length=URL_LENGTH, null=True)
    origin =  models.URLField(max_length=URL_LENGTH, null=True)
    description = models.TextField(max_length=CONTENT_LENGTH, null=True, blank=True)
    content_type = models.CharField(max_length=SHORT_LENGTH, null=True)
    content = models.TextField(max_length=CONTENT_LENGTH, null=True, blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='author', null=True, blank=True)
    count = models.IntegerField(null=True)
    comments = models.URLField(max_length=URL_LENGTH, null=True)
    published = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    visibility = models.CharField(max_length=SHORT_LENGTH, default="PUBLIC", null=False)

    def __str__(self):
        return self.title

class Comment(models.Model):
    type = models.CharField(max_length=SHORT_LENGTH, default="comment")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='comment_author')
    comment = models.TextField(max_length=CONTENT_LENGTH, null=False)
    contentType = models.CharField(max_length=SHORT_LENGTH, null=False)
    published = models.DateTimeField(auto_now_add=True)
    commentId = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comment_post')

    def __str__(self):
        return self.author.displayName + " commented"
   
    
class Comments(models.Model):
    type = models.CharField(max_length=SHORT_LENGTH, default="comments")
    page = models.IntegerField(null=True)
    size = models.IntegerField(null=True)

    def __str__(self):
        return self.author.displayName + " commented"
    
class Node(models.Model):
    node_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    host = models.CharField(max_length=SHORT_MAX_LENGTH, default="127.0.0.1:8000")
    node_name = models.CharField(max_length=100, blank=True)
    node_cred = models.CharField(max_length=100, blank=True)
    api_url = models.URLField(max_length=SHORT_MAX_LENGTH, blank=True)
    
class RemoteServer(models.Model):
    url = models.URLField(max_length=MAX_LENGTH)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.url