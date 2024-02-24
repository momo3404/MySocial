from rest_framework import serializers
from .models import *

class AuthorSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=30)
    url_id = serializers.URLField(max_length=200)  
    author_id = serializers.UUIDField(format='hex_verbose', required=False, allow_null=True)  
    display_name = serializers.CharField(max_length=200)  
    host = serializers.URLField(max_length=200)  
    github = serializers.URLField(max_length=200, allow_blank=True, allow_null=True)  
    profile_url = serializers.URLField(max_length=200)  
    profile_image = serializers.URLField(max_length=200)  
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)

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
        instance.url_id = validated_data.get('url_id', instance.url_id)
        instance.author_id = validated_data.get('author_id', instance.author_id)
        instance.display_name = validated_data.get('display_name', instance.display_name)
        instance.host = validated_data.get('host', instance.host)
        instance.github = validated_data.get('github', instance.github)
        instance.profile_url = validated_data.get('profile_url', instance.profile_url)
        instance.profile_image = validated_data.get('profile_image', instance.profile_image)
        instance.save()
        return instance
    
    class Meta:
        model = Author
        fields = ['type', 'url_id', 'author_id', 'display_name', 'host', 'github', 'profile_url', 'profile_image']