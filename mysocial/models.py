from django.db import models

# Create your models here.

class Post(models.Model):
    post_content = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")