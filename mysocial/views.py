from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from requests.auth import HTTPBasicAuth
from rest_framework import status, generics
from rest_framework.generics import RetrieveUpdateAPIView
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import requests
import uuid
import json

from decouple import config

from .forms import RegisterForm, RemoteServerForm
from .models import *
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

@login_required
@require_POST
def follow(request, author_id):
    user_author = request.user.author
    target_author = Author.objects.get(authorId=author_id)
    if not FollowRequest.objects.filter(actor=user_author, object=target_author).exists():
        FollowRequest.objects.create(actor=user_author, object=target_author, summary="Follow request")
    return redirect('mysocial:public_profile', author_id=author_id)

@login_required
@require_POST
def unfollow(request, author_id):
    user_author = request.user.author
    target_author = Author.objects.get(authorId=author_id)
    Follower.objects.filter(author=target_author, follower=user_author).delete()
    return redirect('mysocial:public_profile', author_id=author_id)

@login_required
def inbox(request, authorId):
    try:
        user_author = request.user.author
        if str(user_author.authorId) != str(authorId):
            raise Http404("Access denied!")

        follow_requests = FollowRequest.objects.filter(object=user_author)
        return render(request, 'base/mysocial/follow_requests.html', {'author': user_author,'follow_requests': follow_requests})
    except Author.DoesNotExist:
        raise Http404("Author not found!")

@login_required
@csrf_exempt  
def process_follow_request(request, author_id):
    print("Called")
    if request.method == 'POST':
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')

        try:
            follow_request = FollowRequest.objects.get(id=request_id)

            if action == 'approve':
                Follower.objects.create(author=follow_request.object, follower=follow_request.actor)

            follow_request.delete()

            return HttpResponseRedirect(reverse('mysocial:follow_requests', args=[author_id]))

        except FollowRequest.DoesNotExist:
            return HttpResponseRedirect(reverse('mysocial:follow_requests', args=[author_id]))

    return HttpResponseRedirect(reverse('mysocial:follow_requests', args=[author_id]))

class CustomLoginView(LoginView):
    template_name = 'base/registration/login.html'

    def get_success_url(self):
        user = self.request.user
        try:
            author_profile = user.author
            return reverse('mysocial:public_profile', kwargs={'author_id': author_profile.authorId})
        except Author.DoesNotExist:
            return reverse('mysocial:index')  

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
    except ValueError:
        # if ID not a valid UUID
        raise Http404("Invalid Author ID")

    author = get_object_or_404(Author, authorId=author_uuid)
    posts = Post.objects.filter(author=author).order_by('-published')
    print(posts)
    already_following = False
    viewing_own_profile = False
    if request.user.is_authenticated:
        try:
            user_author = request.user.author
            viewing_own_profile = user_author.authorId == author_uuid
            already_following = Follower.objects.filter(author=author, follower=user_author).exists()
            follow_requested = FollowRequest.objects.filter(actor=user_author, object=author).exists()
            print(already_following)
        except Author.DoesNotExist:
            pass

    context = {
        'author': author,
        'posts': posts,
        'already_following': already_following,
        'follow_requested': follow_requested,
        'viewing_own_profile': viewing_own_profile,
    }
    
    return render(request, 'base/mysocial/public_profile.html', context)


def edit_display_name(request, author_id):
    author = get_object_or_404(Author, authorId=author_id)

    if request.method == 'POST':
        new_display_name = request.POST.get('displayName')
        author.displayName = new_display_name
        author.save()
        return redirect('mysocial:public_profile', author_id=author_id)

    return render(request, 'base/mysocial/edit_display_name.html', {'author': author})
    
    
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


class PostListCreateView(View):
    template_name = 'base/mysocial/stream_posts.html'

    def get(self, request, authorId):
        posts = Post.objects.all().order_by('-published')
        author = get_object_or_404(Author, authorId=authorId)
        context = {
            'posts': posts,
            'author': author,
        }
        return render(request, self.template_name, context)

    def post(self, request, authorId):
        post_id = request.POST.get('post_id')
        title = request.POST.get('title')
        content = request.POST.get('content')
        author = get_object_or_404(Author, authorId=authorId)

        if post_id:
            # Update existing post
            post = get_object_or_404(Post, pk=post_id)
            post.title = title
            post.content = content
            post.save()
        else:
            # Create new post
            if title and content:
                new_post = Post.objects.create(title=title, content=content, author=author)
                post_url = reverse('mysocial:post_detail', kwargs={'authorId': authorId, 'post_id': new_post.postId})
                new_post.url = request.build_absolute_uri(post_url)
                new_post.save()
            else:
                # Handle missing title or content for new post scenario
                posts = Post.objects.all().order_by('-published')
                context = {
                    'posts': posts,
                    'author': author,
                    'error_message': 'Please fill out all the information required',
                }
                return render(request, self.template_name, context)

        # Redirect to the posts list to see changes
        return redirect(reverse('mysocial:posts_by_author', kwargs={'authorId': authorId}))

class PostDetailView(View):
    template_name = 'base/mysocial/stream_posts.html'

    def get(self, request, authorId, post_id):
        post = get_object_or_404(Post, postId=post_id)
        author = get_object_or_404(Author, authorId=authorId)
        context = {'post': post, 'author': author}
        return render(request, 'base/mysocial/post_detail.html', context)

    def delete(self, request, authorId, post_id):
            post = get_object_or_404(Post, postId=post_id)
            author = get_object_or_404(Author, authorId=authorId)

            if request.user.author == author and post.author == author:
                post.delete()
                return HttpResponse('Post deleted', status=204)
            else:
                return HttpResponse('Forbidden', status=403)

    def put(self, request, authorId, post_id):
            post = get_object_or_404(Post, postId=post_id)
            author = get_object_or_404(Author, authorId=authorId)

            if request.user.author == author and post.author == author:
                data = json.loads(request.body)
                post.title = data.get('title', post.title)
                post.content = data.get('content', post.content)
                post.save()
                return HttpResponse('Post updated', status=200)
            else:
                return HttpResponse('Forbidden', status=403)

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, postId=post_id)
    user_author = request.user.author

    existing = Like.objects.filter(author=user_author, object_url=post.url).first()

    if not existing:
        Like.objects.create(author=user_author, object_url=post.url, summary=f"{user_author.displayName} Likes your post")
        post.likesCount += 1
        post.save()
    else:
        existing.delete()
        post.likesCount -= 1
        post.save()

    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return HttpResponseRedirect(referer_url)
    else:
        return HttpResponseRedirect('/')

    
def fetch_github_activity(request):
    github_token = config('GITHUB_TOKEN')
    headers = {'Authorization': f'token {github_token}'}
    url = 'https://api.github.com/users/archip1/events/public'
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        events = response.json()
        return render(request, 'activity/github_activity.html', {'events': events})
    else:
        return HttpResponse("Failed to fetch GitHub activity", status=500)

