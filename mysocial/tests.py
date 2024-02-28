from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Author, Node, User
import uuid

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
