from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import *
import uuid
from django.core.exceptions import ObjectDoesNotExist
import base64
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
import json
class AuthorTesting(TestCase):
    def setUp(self):
        self.user = User.objects.create(username = "TestUser", password = "TestPassword")

        self.author = Author.objects.create(user=self.user)

    def test_author_model_is_valid(self):
        d = self.author
        self.assertTrue(isinstance(d, Author))

    def test_get_authors(self):
        response = self.client.get(reverse('mysocial:authors'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['displayName'], 'Test Author')

class AuthorViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        self.author = Author.objects.create(displayName='Test Author', user=self.user)
        self.url = reverse('mysocial:authors-detail', kwargs={'authorId': self.author.authorId})

    def test_get_author(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['displayName'], 'Test Author')

class NodeInfoAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        self.node = Node.objects.create(node_name="TestNode")
        self.url = reverse('mysocial:node_info', kwargs={'node_name': self.node.node_name})

    def test_get_node_info(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['node_name'], 'TestNode')   

class PostTesting(TestCase):
    def setUp(self):
        # jpeg test image
        with open('mysocial/test_image.jpeg', 'rb') as f:
            image_data = f.read()
            image_data_jpg = base64.b64encode(image_data)

        self.user2 = User.objects.create(
                username = "Test2",
                password = "1234"
                )

        self.author2 = Author.objects.create(user=self.user2)

        self.post1 = Post.objects.create(
            title="example post 1",
            description="This post is an example",
            content_type="image/jpeg;base64",
            content="testing... 1,2,3",
            image=ContentFile(base64.b64decode(image_data_jpg), name='test_image_1'),
            author=self.author2,
            likesCount=5,
            visibility="PUBLIC"
        )

    def test_post_model_is_valid_png(self):
        self.assertTrue(isinstance(self.post1, Post))

    def test_post_model_str(self):
        self.assertEqual(str(self.post1), "example post 1")


class ModelTesting(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="Test1", password="1234")
        self.user2 = User.objects.create(username="Test2", password="1234")
        self.author1 = Author.objects.create(user=self.user1, displayName="Author 1", url=f"http://example.com/author/{uuid.uuid4()}")
        self.author2 = Author.objects.create(user=self.user2, displayName="Author 2", url=f"http://example.com/author/{uuid.uuid4()}")
        self.followers = Follower.objects.create(author=self.author1, follower=self.author2)
        self.follow_request = FollowRequest.objects.create(type="Follow", summary="Test follow request", actor=self.author2, object=self.author1)
        
        with open('mysocial/test_image.jpeg', 'rb') as f:
            image_data = f.read()
            image_data_jpg = base64.b64encode(image_data)
        self.post = Post.objects.create(
            title="Test Post",
            description="This is a test post",
            content_type="image/jpeg;base64",
            content="Testing content",
            image=ContentFile(base64.b64decode(image_data_jpg), name='test_image_1'),
            author=self.author1,
            likesCount=5,
            visibility="PUBLIC"
        )
        self.comment = Comment.objects.create(
            type="comment",
            author=self.author1,
            comment="Test comment",
            contentType="text/plain",
            post=self.post
        )
        self.node = Node.objects.create(node_name="Test Node", url="127.0.0.1:8000")
        self.like = Like.objects.create(
            context="https://www.w3.org/ns/activitystreams",
            summary="Test like",
            type="Like",
            author=self.author2,
            object_url="http://example.com/post"
        )

    def test_follower_model_is_valid(self):
        self.assertTrue(isinstance(self.followers, Follower))

    def test_follow_request_model_is_valid(self):
        self.assertTrue(isinstance(self.follow_request, FollowRequest))

    def test_post_model_is_valid(self):
        self.assertTrue(isinstance(self.post, Post))

    def test_comment_model_is_valid(self):
        self.assertTrue(isinstance(self.comment, Comment))

    def test_node_model_is_valid(self):
        self.assertTrue(isinstance(self.node, Node))

    def test_like_model_is_valid(self):
        self.assertTrue(isinstance(self.like, Like))

class FollowandLikeTesting(TestCase):
    def setUp(self):
        author1_url = "http://example.com/authors/" + str(uuid.uuid4())
        author2_url = "http://example.com/authors/" + str(uuid.uuid4())
        author3_url = "http://example.com/authors/" + str(uuid.uuid4())

        self.author1 = Author.objects.create(url=author1_url)
        self.author2 = Author.objects.create(url=author2_url)
        self.author3 = Author.objects.create(url=author3_url)

    def test_followers_get(self):
        author1_url = "http://example.com/authors/" + str(uuid.uuid4())
        author2_url = "http://example.com/authors/" + str(uuid.uuid4())
        author1 = Author.objects.create(url=author1_url)
        author2 = Author.objects.create(url=author2_url)

        follower = Follower.objects.create(author=author1, follower=author2)

        # check Follower instance is created successfully
        self.assertIsNotNone(follower)

    def test_likes(self):
        context = "https://www.w3.org/ns/activitystreams"
        object_link = "http://127.0.0.1:8000/api/authors/9de17f29c12e8f97bcbbd34cc908f1baba40658e/posts/764efa883dda1e11db47671c4a3bbd9e"

        like = Like.objects.create(
            context=context,
            author=self.author1,
            object_url=object_link
        )

        self.assertEqual(Like.objects.count(), 1)

        self.author1.likes_given.add(like)
        self.assertEqual(self.author1.likes_given.count(), 1)

class CommentTestCase(TestCase):
    def setUp(self):
        self.author = Author.objects.create(displayName="John Doe")

        self.post = Post.objects.create(
            title="Test Post",
            content="This is a test post.",
            author=self.author
        )

    def test_create_comment(self):
        comment = Comment.objects.create(
            author=self.author,
            comment="This is a test comment.",
            contentType="text/plain",
            post=self.post
        )

        self.assertIsNotNone(comment)
