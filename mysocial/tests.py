from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import *
import uuid
from django.core.exceptions import ObjectDoesNotExist

class AuthorListTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        Author.objects.create(displayName='Test Author', user=self.user)

    def test_get_authors(self):
        response = self.client.get(reverse('mysocial:authors'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
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

    def test_delete_author(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Author.objects.filter(pk=self.author.pk).exists())

    def test_update_author_invalid_data(self):
        invalid_data = {'displayName': ''}
        response = self.client.put(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_author_valid_data(self):
        updated_data = {'displayName': 'Updated Test Author'}
        response = self.client.put(self.url, updated_data, format='json')
        self.author.refresh_from_db()
        self.assertEqual(self.author.displayName, 'Updated Test Author')
        
class NodeInfoAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        self.node = Node.objects.create(node_name="TestNode", user=self.user, host="127.0.0.1:8000")
        self.url = reverse('mysocial:node_info', kwargs={'node_name': self.node.node_name})

    def test_get_node_info(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['node_name'], 'TestNode')       

class LikesViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpassword')
        self.author = Author.objects.create(displayName='Test Author', user=self.user)
        postid = uuid.uuid1()
        self.post = Post.objects.create(postId=postid, author=self.author,  url=f'http://127.0.0.1:8000/posts/{postid}/like/')
        likes = Like.objects.filter(object_url=f'http://127.0.0.1:8000/posts/{postid}/like/').order_by('-timestamp')
        self.like1 = Like.objects.create(object_url=self.post.url, author=self.author)
        self.like2 = Like.objects.create(object_url=self.post.url, author=self.author)

    def test_get_likes_success(self):
        postid = uuid.uuid1()
        url = reverse('mysocial:like_post', kwargs={'post_id': postid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['type'], 'likes')
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(data['count'], 2)

    def test_get_likes_post_not_found(self):
        postid = uuid.uuid1()
        url = reverse('mysocial:like_post', kwargs={'authorId': 'nonexistentauthor', 'post_id': postid})
        self.assertRaises(ObjectDoesNotExist)

class CommentsViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        postid = uuid.uuid1()
        self.author_id = uuid.uuid4()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.author = Author.objects.create(authorId=self.author_id, displayName='Test Author', user=self.user)
        self.post = Post.objects.create(postId=postid, author=self.author,  url=f'http://127.0.0.1:8000/posts/{postid}/')
        self.comment1 = Comment.objects.create(author=self.author, comment='Test Comment 1', contentType='text/plain', post=self.post)
        self.comment2 = Comment.objects.create(author=self.author, comment='Test Comment 2', contentType='text/plain', post=self.post)

    def test_get_comments_success(self):
        postid = uuid.uuid1()
        url = reverse('mysocial:comments', kwargs={'authorId': self.author_id, 'post_id': postid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['type'], 'comments')
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['size'], 5)
        self.assertEqual(len(data['comments']), 2)

    def test_create_comment_success(self):
        postid = uuid.uuid1()
        self.client.force_login(self.user)
        url = reverse('mysocial:comments', kwargs={'authorId': self.author_id, 'post_id': postid})
        data = {'comment': 'New Test Comment', 'contentType': 'text/plain'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        new_comment = Comment.objects.latest('published')
        self.assertEqual(new_comment.author, self.author)
        self.assertEqual(new_comment.comment, 'New Test Comment')
        self.assertEqual(new_comment.contentType, 'text/plain')
        self.assertEqual(new_comment.post, self.post)

    def test_create_comment_invalid_data(self):
        self.client.force_login(self.user)
        postid = uuid.uuid1()
        url = reverse('mysocial:comments', kwargs={'authorId': self.author_id, 'post_id': postid})
        data = {'contentType': 'text/plain'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def tearDown(self):
        self.user.delete()
        self.author.delete()
        self.post.delete()
        self.comment1.delete()
        self.comment2.delete()

class InboxViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.author_id = uuid.uuid4() 
        self.author = Author.objects.create(authorId= self.author_id, displayName='Test Author', user=self.user)
        self.inbox_item1 = Inbox.objects.create(author=self.author, inbox_item={'type': 'follow', 'data': 'Follow request'})
        self.inbox_item2 = Inbox.objects.create(author=self.author, inbox_item={'type': 'like', 'data': 'Like notification'})

    def test_get_inbox_success(self):
        url = reverse('mysocial:inbox', kwargs={'authorId':  self.author_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['type'], 'inbox')
        self.assertEqual(data['author'], self.author_id)
        self.assertEqual(len(data['items']), 2)

    def test_create_inbox_item_success(self):
        url = reverse('mysocial:inbox', kwargs={'authorId':  self.author_id})
        data = {'type': 'post', 'data': 'New post notification'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Inbox.objects.filter(author=self.author, inbox_item=data).exists())

    def test_create_inbox_item_invalid_data(self):
        url = reverse('mysocial:inbox', kwargs={'authorId':  self.author_id})
        data = {'data': 'New post notification'}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def test_delete_inbox_items_success(self):
        url = reverse('mysocial:inbox', kwargs={'authorId':  self.author_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Inbox.objects.filter(author=self.author).count(), 0)

