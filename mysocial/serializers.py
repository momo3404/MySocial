from rest_framework import serializers
from .models import *

class AuthorSerializer(serializers.Serializer):
    author_id = serializers.CharField()

    def create(self, validated_data):
        """
        Create and return a new `author` instance, given the validated data
        """
        return Author.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """
        Update and return an existing `author` instance, given the validated data
        """
        instance.author_id = validated_data.get('author_id', instance.question_text)
        instance.save()
        return instance