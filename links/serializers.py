# Create your serializers here.
from django.forms import widgets
from rest_framework import serializers
from links.models import Link
from django.contrib.auth.models import User
import logging


class Wikifetch(object):
    def __init__(self, title, description, url):
        self.title = title
#        self.submitter = submitter
        self.description = description
        self.url = url

class Item(object):
    def __init__(self, title, score, user, comments, timeAgo, itemId, url, itemInfo):
        self.title = title
#        self.submitter = submitter
        self.score = score
        self.user = user
        self.comments = comments
        self.timeAgo = timeAgo
        self.itemId = itemId
        self.itemInfo = itemInfo
        self.url = url


class LinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Link
        fields = ('title', 'description', 'submitter', 'url', 'votes', 'linksource')


class UserSerializer(serializers.ModelSerializer):
    link = serializers.PrimaryKeyRelatedField(many=True)

    class Meta:
        model = User
        fields = ('id', 'username')

class ItemSerializer(serializers.Serializer):
    url = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    score = serializers.CharField(required=False)
    user = serializers.CharField(required=False)
    comments = serializers.CharField(required=False)
    timeAgo = serializers.CharField(required=False)
    itemId = serializers.CharField(required=False)
    itemInfo = serializers.CharField(required=False)
  
    def restore_object(self, attrs, instance=None):
        """
        Restore object for json response
        """
        if instance:
            # Update existing instance
            instance.title = attrs.get('title', instance.title)
            instance.score = attrs.get('score', instance.score)
            instance.user = attrs.get('user', instance.user)
            instance.comments = attrs.get('comments', instance.comments)
            instance.timeAgo = attrs.get('timeAgo', instance.timeAgo)
            instance.itemId = attrs.get('itemId', instance.itemId)
            instance.itemInfo = attrs.get('itemInfo', instance.itemInfo)
            instance.url = attrs.get('url', instance.linenos)
            return instance

        # Create new instance
        return Item(**attrs)


'''
    def restore_object(self, attrs, instance=None):
        """
        Restore object for json response
        """
        if instance:
            # Update existing instance
            instance.title = attrs.get('title', instance.title)
            instance.description = attrs.get('description', instance.description)
            instance.url = attrs.get('url', instance.url)
            return instance

        # Create new instance
        return Link(**attrs)
'''