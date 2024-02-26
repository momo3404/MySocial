from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from requests.auth import HTTPBasicAuth
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

import requests
import uuid

from .forms import RegisterForm, RemoteServerForm
from .models import RemoteServer, Author, Follower, FollowRequest, Post, Comment, Node
from .serializers import AuthorSerializer, FollowerSerializer, FollowRequestSerializer, PostSerializer, CommentSerializer

# Create your views here.
def index(request):
    return render(request, 'base/home.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False 
            user.save()
            return render(request, 'base/registration/pending_approval.html')
    else:
        form = RegisterForm()
    return render(request, 'base/registration/register.html', {'form': form})


def add_server(request):
    if request.method == 'POST':
        form = RemoteServerForm(request.POST)
        if form.is_valid():
            new_remote_server = form.save(commit=False)
            data = connect_to_remote_server(new_remote_server.id)
            
            if data is not None:
                print("Successfully connected to the remote server and retrieved data.")
            else:
                print("Failed to connect to the remote server.")
            return redirect('../')  
    else:
        form = RemoteServerForm()
    return render(request, 'base/remote/add_server.html', {'form': form})


def connect_to_remote_server(remote_server_id):
    try:
        remote_server = RemoteServer.objects.get(id=remote_server_id)
        request_url = f"{remote_server.url}/api/data"
        response = requests.get(request_url, auth=HTTPBasicAuth(remote_server.username, remote_server.password))
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Failed to connect to {remote_server.url}. Status code: {response.status_code}")
            return None
    except RemoteServer.DoesNotExist:
        print("Remote server not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
       
class AuthorList(APIView):
    def get(self, request, format=None):
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

class AuthorView(APIView):
    def get_object(self, authorId):
        try:
            return Author.objects.get(authorId=authorId)
        except Author.DoesNotExist:
            raise Http404
        
    def get(self, request, authorId, format=None):
        author = self.get_object(authorId)
        serializer = AuthorSerializer(author)
        return Response(serializer.data)
    
    def put(self, request, authorId, format=None):
        author = self.get_object(authorId)
        serializer = AuthorSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class FollowerList(APIView):
    def get(self, request, authorId=None, format=None):
            if authorId is not None:
                followers = Follower.objects.filter(follower__authorId=authorId)
            else:
                followers = Follower.objects.all()
            serializer = FollowerSerializer(followers, many=True)
            return Response(serializer.data)
    
class FollowDetail(APIView):
    def get_object(self, authorId):
        try:
            return Author.objects.get(authorId=authorId)
        except Author.DoesNotExist:
            raise Http404
    
    def get(self, request, authorId, follower):
        exists = Follower.objects.filter(author_id=authorId, follower_id=follower).exists()
        return Response({'follows': exists})
    
    def delete(self, request, authorId, follower):
        Follower.objects.filter(author_id=authorId, follower_id=follower).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def put(self, request, authorId, follower):
        author = self.get_object(authorId)
        follower_obj = self.get_object(follower)
        Follower.objects.get_or_create(author=author, follower=follower_obj)
        return Response(status=status.HTTP_201_CREATED)

def public_profile(request, author_id):
    try:
        # author_id string from URL to a UUID object
        author_uuid = uuid.UUID(str(author_id))
        author = get_object_or_404(Author, authorId=author_uuid)
        return render(request, 'base/mysocial/public_profile.html', {'author': author})
    except ValueError:
        # if ID not a valid UUID
        raise Http404("Invalid Author ID")
    
    
class NodeInfoAPIView(APIView):
    def get(self, request, node_name):
        try:
            # Retrieve the node based on the node_name
            node = Node.objects.get(node_name=node_name)
            # Retrieve information about the node
            data = {
                'node_id': node.node_id,
                'host': node.host,
                'node_name': node.node_name,
                'node_cred': node.node_cred,
                'api_url' : node.api_url,
                # Add other node information as needed
            }
            return Response(data)
        except Node.DoesNotExist:
            return Response({'error': 'Node not found'}, status=404)
        
class NodeConnection(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, node_name):
        # Your existing logic to retrieve node information
        try:
            print(request.user.username)
            print(node_name)
            sender_node = Node.objects.get(node_name=request.user.username)
            receiver_node = Node.objects.get(node_name=node_name)
            data = {
                'sender_node_id': sender_node.node_id,
                'sender_host': sender_node.host,
                'sender_node_name': sender_node.node_name,
                'sender_node_cred': sender_node.node_cred,
                'sender_api_url' : sender_node.api_url,
                
                'receiver_node_id': receiver_node.node_id,
                'receiver_host': receiver_node.host,
                'receiver_node_name': receiver_node.node_name,
                'receiver_node_cred': receiver_node.node_cred,
                'receiver_api_url' : receiver_node.api_url, 
            }
            return Response(data)
        except Node.DoesNotExist:
            return Response({'error': 'Node not found'}, status=status.HTTP_404_NOT_FOUND)
    

