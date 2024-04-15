from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Author, Post, Like, FollowRequest, Comment
import uuid

class AuthorCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='user@test.com', password='testpass')
        self.author = Author.objects.create(displayName='Author1', user=self.user, url=f"http://example.com/author/{uuid.uuid4()}")

    def test_create_author(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('mysocial:authors')
        data = {'displayName': 'New Author', 'user': self.user.id, 'url': f"http://example.com/author/{uuid.uuid4()}"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_author(self):
        url = reverse('mysocial:authors-detail', kwargs={'authorId': self.author.authorId})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_author(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('mysocial:authors-detail', kwargs={'authorId': self.author.authorId})
        data = {'displayName': 'Updated Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_author(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('mysocial:authors-detail', kwargs={'authorId': self.author.authorId})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class PostCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser2', email='user2@test.com', password='testpass2')
        self.author = Author.objects.create(displayName='Author2', user=self.user, url=f"http://example.com/author/{uuid.uuid4()}")
        self.post = Post.objects.create(title='Initial Post', content='Initial content', author=self.author, visibility='PUBLIC')

    def test_create_post(self):
        self.client.login(username='testuser2', password='testpass2')
        url = reverse('mysocial:multiple_posts', kwargs={'authorId': self.author.authorId})
        data = {'title': 'New Post', 'content': 'Content of the new post', 'author': self.author.id, 'visibility': 'PUBLIC'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_post(self):
        url = reverse('mysocial:single_post', kwargs={'authorId': self.author.authorId, 'post_id': self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_post(self):
        self.client.login(username='testuser2', password='testpass2')
        url = reverse('mysocial:single_post', kwargs={'authorId': self.author.authorId, 'post_id': self.post.id})
        data = {'title': 'Updated Post', 'content': 'Updated content'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_post(self):
        self.client.login(username='testuser2', password='testpass2')
        url = reverse('mysocial:single_post', kwargs={'authorId': self.author.authorId, 'post_id': self.post.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class CommentCRUDTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser3', email='user3@test.com', password='testpass3')
        self.author = Author.objects.create(displayName='Author3', user=self.user, url=f"http://example.com/author/{uuid.uuid4()}")
        self.post = Post.objects.create(title='Initial Post', content='Initial content', author=self.author, visibility='PUBLIC')
        self.comment = Comment.objects.create(comment='Initial Comment', post=self.post, author=self.author, contentType='text/plain')

    def test_create_comment(self):
        self.client.login(username='testuser3', password='testpass3')
        url = reverse('mysocial:comments_post', kwargs={'authorId': self.author.authorId, 'post_id': self.post.id})
        data = {'comment': 'New Comment', 'post': self.post.id, 'author': self.author.id, 'contentType': 'text/plain'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_comment(self):
        url = reverse('mysocial:comments_post', kwargs={'authorId': self.author.authorId, 'post_id': self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_comment(self):
        self.client.login(username='testuser3', password='testpass3')
        url = reverse('mysocial:comments_post', kwargs={'authorId': self.author.authorId, 'post_id': self.post.id, 'comment_id': self.comment.id})
        data = {'comment': 'Updated Comment'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_comment(self):
        self.client.login(username='testuser3', password='testpass3')
        url = reverse('mysocial:comments_post', kwargs={'authorId': self.author.authorId, 'post_id': self.post.id, 'comment_id': self.comment.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class FollowRequestTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', email='user1@test.com', password='testpass1')
        self.user2 = User.objects.create_user(username='user2', email='user2@test.com', password='testpass2')
        self.author1 = Author.objects.create(displayName='Author1', user=self.user1, url=f"http://example.com/author/{uuid.uuid4()}")
        self.author2 = Author.objects.create(displayName='Author2', user=self.user2, url=f"http://example.com/author/{uuid.uuid4()}")

    def test_send_follow_request(self):
        self.client.login(username='user1', password='testpass1')
        url = reverse('mysocial:process_follow_request')
        data = {'summary': 'Author1 wants to follow Author2', 'actor': self.author1.id, 'object': self.author2.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_accept_follow_request(self):
        follow_request = FollowRequest.objects.create(summary="Author1 wants to follow Author2", actor=self.author1, object=self.author2)
        self.client.login(username='user2', password='testpass2')
        # Assuming an endpoint exists to accept follow requests
        url = reverse('mysocial:accept_follow_request', kwargs={'request_id': follow_request.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reject_follow_request(self):
        follow_request = FollowRequest.objects.create(summary="Author1 wants to follow Author2", actor=self.author1, object=self.author2)
        self.client.login(username='user2', password='testpass2')
        # Assuming an endpoint exists to reject follow requests
        url = reverse('mysocial:reject_follow_request', kwargs={'request_id': follow_request.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class LikeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1like', email='user1like@test.com', password='testpass1like')
        self.user2 = User.objects.create_user(username='user2like', email='user2like@test.com', password='testpass2like')
        self.author1 = Author.objects.create(displayName='Author1like', user=self.user1, url=f"http://example.com/author/{uuid.uuid4()}")
        self.author2 = Author.objects.create(displayName='Author2like', user=self.user2, url=f"http://example.com/author/{uuid.uuid4()}")
        self.post = Post.objects.create(title='Post for Like', content='This is a likable post.', author=self.author2, visibility='PUBLIC')

    def test_like_post(self):
        self.client.login(username='user1like', password='testpass1like')
        url = reverse('mysocial:like_post', kwargs={'post_id': self.post.id})
        data = {'summary': 'Author1like likes this post', 'author': self.author1.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
