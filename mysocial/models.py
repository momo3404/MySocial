from django.db import models
from django.contrib.auth.models import User
import uuid

MAX_LENGTH = 1000
SHORT_MAX_LENGTH = 200

# Create your models here.
class Author(models.Model):
    author_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False) # Removed max_length, added auto-generating UUIDs
    display_name = models.CharField(max_length=MAX_LENGTH)
    url_id = models.URLField(max_length=MAX_LENGTH, unique=True)
    profile_url = models.URLField(max_length=MAX_LENGTH) 
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author', blank=False) # this is for user/author creation got rid of: null=True  bcz cant be empty

    def __str__(self):
        return self.display_name

class Post(models.Model):
    text = models.CharField(max_length=SHORT_MAX_LENGTH)
    pub_date = models.DateTimeField("date published")
    content = models.TextField(max_length=MAX_LENGTH, null=True, blank=True)
    # foreign key to author
    author = models.ForeignKey(Author, on_delete=models.CASCADE, to_field='author_id', related_name='posts') # remove , null=True bcz u cant have a post without an author

    # null = True means empty values for the field will be set as NULL
    # blank = True means the field will not be required

    title = models.CharField(max_length=MAX_LENGTH, null=True)
    url_id = models.URLField(max_length=MAX_LENGTH, unique=True, null=True)
    post_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # Removed max_length, added default
    description = models.TextField(max_length=MAX_LENGTH, null=True, blank=True)

    def __str__(self):
        return self.text

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
