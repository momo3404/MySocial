from django.db import models
from django.contrib.auth.models import User

MAX_LENGTH = 1000

# Create your models here.
    
class Author(models.Model):
    author_id = models.UUIDField(max_length=MAX_LENGTH, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=MAX_LENGTH)

    url_id = models.URLField(max_length=MAX_LENGTH, unique=True, null=False)
    profile_url = models.URLField(max_length=MAX_LENGTH) 
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author', null=True, blank=False) # this is for user/author creation

    def __str__(self):
        return self.display_name
    
class Post(models.Model):
    text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")
    content = models.TextField(max_length=MAX_LENGTH, null=True, blank=True)
    # foreign key to author
    author = models.ForeignKey(Author, on_delete=models.CASCADE, to_field='author_id', related_name='posts', null=True)

    # null = True means empty values for the field will be set as NULL
    # blank = True means the field will not be required

    title =  models.CharField(max_length=MAX_LENGTH, null=True)
    url_id = models.URLField(max_length=MAX_LENGTH, unique=True, null=True)
    post_id = models.UUIDField(max_length=MAX_LENGTH, unique=True, null=True)
    description = models.TextField(max_length=MAX_LENGTH, null=True, blank=True)

    def __str__(self):
        return self.text