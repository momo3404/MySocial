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
    