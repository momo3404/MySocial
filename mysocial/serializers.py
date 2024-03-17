from rest_framework import serializers
from .models import *

class AuthorSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=30)
    id = serializers.UUIDField(source='authorId',format='hex_verbose', required=False, allow_null=True)  
    url = serializers.URLField(max_length=200)  
    host = serializers.URLField(max_length=200)  
    displayName = serializers.CharField(max_length=200)  
    github = serializers.URLField(max_length=200, allow_blank=True, allow_null=True)  
    profileImage = serializers.URLField(max_length=200)  
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)

    class Meta:
        model = Author
        fields = ['type', 'id', 'url', 'host', 'displayName', 'github', 'profileImage']
        
    def create(self, validated_data):
        """
        Create and return a new `author` instance, given the validated data
        """
        validated_data['authorId'] = validated_data.pop('id', None)
        return Author.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing `author` instance, given the validated data
        """
        validated_data['authorId'] = validated_data.pop('id', instance.authorId)
        instance = super().update(instance, validated_data)
        instance.save()
        return instance
    
    
class LikeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['context', 'summary', 'type', 'author', 'object_url', 'timestamp']
    
class FollowerSerializer(serializers.ModelSerializer):
    follower = AuthorSerializer(read_only=True)
    
    class Meta:
        model = Follower
        fields = ['follower']
        

class FollowRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowRequest
        fields = ['id', 'type', 'summary', 'actor', 'object']
        
class PostSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), allow_null=True)
    id = serializers.UUIDField(source='postId',format='hex_verbose', required=False, allow_null=True)  
    class Meta:
        model = Post
        fields = ['type', 'id' ,'title', 'url', 'source', 'origin', 'description', 'content_type', 'content', 'author', 'published', 'visibility']
    def create(self, validated_data):
        """
        Create and return a new `Post` instance, given the validated data.
        """
        validated_data['postId'] = validated_data.pop('id', None)
        return Post.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing `Post` instance, given the validated data.
        """
        validated_data['postId'] = validated_data.pop('id', instance.postId)
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