from rest_framework import serializers
from .models import *

class AuthorSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=30)
    authorId = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True)  
    url = serializers.URLField(max_length=200)  
    host = serializers.URLField(max_length=200)  
    displayName = serializers.CharField(max_length=200)  
    github = serializers.URLField(max_length=200, allow_blank=True, allow_null=True)  
    profileImage = serializers.URLField(max_length=200)  
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)

    class Meta:
        model = Author
        fields = ['type', 'authorId', 'url', 'host', 'displayName', 'github', 'profileImage']
        
    def create(self, validated_data):
        """
        Create and return a new `author` instance, given the validated data
        """
        return Author.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing `author` instance, given the validated data
        """
        instance.type = validated_data.get('type', instance.type)
        instance.authorId = validated_data.get('authorId', instance.authorId)
        instance.url = validated_data.get('url', instance.url)
        instance.host = validated_data.get('host', instance.host)
        instance.displayName = validated_data.get('displayName', instance.displayName)
        instance.github = validated_data.get('github', instance.github)
        instance.profileImage = validated_data.get('profileImage', instance.profileImage)
        instance.save()
        return instance
    
    
class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = ['attributes', 'follower']
        

class FollowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowRequest
        fields = ['type', 'summary', 'actor', 'object']
        
class PostSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), allow_null=True)

    class Meta:
        model = Post
        fields = ['type', 'postId' ,'title', 'url', 'source', 'origin', 'description', 'content_type', 'content', 'author', 'published', 'visibility']
    def create(self, validated_data):
        """
        Create and return a new `Post` instance, given the validated data.
        """
        return Post.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing `Post` instance, given the validated data.
        """
        instance.type = validated_data.get('type', instance.type)
        instance.title = validated_data.get('title', instance.title)
        instance.url = validated_data.get('url', instance.url)
        instance.source = validated_data.get('source', instance.source)
        instance.origin = validated_data.get('origin', instance.origin)
        instance.description = validated_data.get('description', instance.description)
        instance.content_type = validated_data.get('content_type', instance.content_type)
        instance.content = validated_data.get('content', instance.content)
        instance.author = validated_data.get('author', instance.author)
        instance.published = validated_data.get('published', instance.published)
        instance.visibility = validated_data.get('visibility', instance.visibility)
        
        instance.save()
        return instance
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all())
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

    class Meta:
        model = Comment
        fields = ['type', 'author', 'comment', 'contentType', 'published', 'commentId', 'post']