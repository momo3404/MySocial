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
from django.db.models import Q
from django.db import IntegrityError
from django.http import JsonResponse
import requests
import uuid
import json
import urllib
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from decouple import config
from django.core.files.base import ContentFile
import base64
from .forms import RegisterForm
from .models import *
from .serializers import AuthorSerializer, FollowerSerializer, FollowRequestSerializer, PostSerializer, CommentSerializer, LikeSerializer
import commonmark
from urllib.parse import urlparse
import re

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


def remote(request):
    nodes = Node.objects.all()
    node_details = []

    for node in nodes:
        node_status = {
            'node_name': node.node_name,
            'node_url': node.url,
            'node_id': node.node_id,
            'authors': []
        }

        try:
            node_response = requests.get(node.url, auth=HTTPBasicAuth(node.username, node.password), timeout=5)
            authors_response = requests.get(node.authors_url, auth=HTTPBasicAuth(node.username, node.password), timeout=5)

            if node_response.status_code == 200:
                node_status['status'] = "Node successfully connected."
            else:
                node_status['status'] = "Could not connect to node. Please inform your server admin."

            if authors_response.status_code == 200:
                authors_data = authors_response.json()
                node_status['authors'] = authors_data.get('items', [])
            else:
                node_status['status'] += " Could not retrieve authors. Please inform your server admin."

        except requests.exceptions.RequestException as e:
            node_status['status'] = "Could not connect to node. Please inform your server admin."

        node_details.append(node_status)

    context = {'node_details': node_details}
    return render(request, 'base/mysocial/remote.html', context)


@login_required
@require_POST
def follow(request, author_id):
    user_author = request.user.author
    target_author = Author.objects.get(authorId=author_id)
    if not FollowRequest.objects.filter(actor=user_author, object=target_author).exists():
        new_request = FollowRequest.objects.create(actor=user_author, object=target_author, summary="Follow request")
        
        actor_data = AuthorSerializer(user_author).data
        object_data = AuthorSerializer(target_author).data

        inbox_item = {
            "type": "Follow",
            "summary": f"{actor_data['displayName']} wants to follow {object_data['displayName']}",
            "actor": actor_data,
            "object": object_data,
        }

        Inbox.objects.create(
            author=target_author,
            inbox_item=json.dumps(inbox_item)
        )
        print(json.dumps(inbox_item))
        
    return redirect('mysocial:public_profile', author_id=author_id)

@login_required
@require_POST
def unfollow(request, author_id):
    user_author = request.user.author
    target_author = Author.objects.get(authorId=author_id)
    Follower.objects.filter(author=target_author, follower=user_author).delete()
    return redirect('mysocial:public_profile', author_id=author_id)

def inbox(request, author_id):
    author = get_object_or_404(Author, authorId=author_id)

    if request.user.author.authorId != author_id and not request.user.is_superuser:
        return render(request, 'error_page.html', {'message': 'You do not have permission to view this inbox.'})

    inbox_items = Inbox.objects.filter(author=author).order_by('-timestamp')
    processed_inbox_items = []
    if inbox_items:
        for item in inbox_items:
            item_data = json.loads(item.inbox_item)
            item_data['inbox_id'] = item.inbox_id 
            processed_inbox_items.append(item_data)

    context = {
        'author': author,
        'inbox_items': processed_inbox_items,
    }

    return render(request, 'base/mysocial/inbox.html', context)

class LikesView(View):
    def get(self, request, authorId, post_id):
        post = get_object_or_404(Post, postId=post_id, author__authorId=authorId)
        likes = Like.objects.filter(object_url=post.url).order_by('-timestamp')
        serializer = LikeSerializer(likes, many=True)

        return JsonResponse({
            "type": "likes",
            "items": serializer.data,
            "count": likes.count()
        })

@method_decorator(csrf_exempt, name='dispatch')
class CommentsView(View):
    def get(self, request, authorId, post_id):
        post = get_object_or_404(Post, postId=post_id, author__authorId=authorId)
        comments = Comment.objects.filter(post=post).order_by('-published')

        page = int(request.GET.get('page', 1))
        size = int(request.GET.get('size', 5))
        start_index = (page - 1) * size
        end_index = page * size

        comments_paged = comments[start_index:end_index]

        serializer = CommentSerializer(comments_paged, many=True)

        return JsonResponse({
            "type": "comments",
            "page": page,
            "size": size,
            "post": post.url,
            "id": request.build_absolute_uri(),
            "comments": serializer.data
        })

    def post(self, request, authorId, post_id):
        post = get_object_or_404(Post, postId=post_id, author__authorId=authorId)
        data = {
            'author': request.user.author.authorId, 
            'post': post.postId,
            'comment': request.POST.get('comment'),
            'contentType': request.POST.get('contentType', 'text/plain'),
        }
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        else:
            return JsonResponse(serializer.errors, status=400)

class InboxView(APIView):
    def get_author(self, authorId):
        try:
            return Author.objects.get(authorId=authorId)
        except Author.DoesNotExist:
            raise Http404("Author not found")

    def get(self, request, authorId, format=None):
        author = self.get_author(authorId)
        inbox_items = Inbox.objects.filter(author=author).order_by('-inbox_item__published')
        paginator = Paginator(inbox_items, 10)  
        page_number = request.query_params.get('page')
        page_obj = paginator.get_page(page_number)

        items = [json.loads(item.inbox_item) for item in page_obj]

        return Response({
            "type": "inbox",
            "author": str(author.authorId),
            "items": items
        })

    def post(self, request, authorId, format=None):
        author = self.get_author(authorId)
        print("GOT HERE")
        data = request.data
        image_post = False

        if data.get('type') == 'post':
            post_id = data.get('id')
            if post_id:
                existing_post = Post.objects.filter(postId=post_id).first()
                if existing_post:
                    return Response({'detail': 'Post already exists.'}, status=status.HTTP_200_OK)
                if data.get('contentType') in ["image/png;base64", "image/jpeg;base64"]:
                    image_post = True
                try:
                    new_post = Post.objects.create(
                        author=author,
                        type=data.get('type', 'post'),
                        title=data.get('title'),
                        url=data.get('url'),
                        source=data.get('source'),
                        origin=data.get('origin'),
                        description=data.get('description'),
                        content_type=data.get('contentType', 'post'),
                        content=data.get('content'),
                        visibility=data.get('visibility', 'PUBLIC'),
                    )
                    if image_post:
                        img_data = base64.b64decode(data.get('content'))
                        image_content = ContentFile(img_data)
                        filename = f"{uuid.uuid4()}.png"  # Generate a unique filename
                        new_post.image.save(filename, image_content)
                        new_post.save()
        
                    inbox_item = Inbox(author=author, inbox_item=json.dumps(data))
                    inbox_item.save()
                    return Response({'detail': 'New post created.'}, status=status.HTTP_201_CREATED)
                except IntegrityError:
                    return Response({'detail': 'IntegrityError, post could not be created.'}, status=status.HTTP_400_BAD_REQUEST)

        if data.get('type') in ["post", "Follow", "Like", "comment", "share-post", "follow"]:
            inbox_item = Inbox(author=author, inbox_item=json.dumps(data))
            inbox_item.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response({"detail": "Invalid data type for inbox."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, authorId, format=None):
        author = self.get_author(authorId)
        Inbox.objects.filter(author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

def extract_uuid_from_url(url):
    match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', url)
    return match.group(0) if match else None

@login_required
@csrf_exempt  
def process_follow_request(request):
    def get_author(authorId, create_remote=False):
        new_author_id = extract_uuid_from_url(authorId) or authorId
        try:
            # new_author_id = authorId.split('/')[-1]
            return Author.objects.get(authorId=new_author_id)
        except Author.DoesNotExist:
            if create_remote:
                return None
            raise Http404("Author not found")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        inbox_item_id = request.POST.get('inbox_item_id')
        author_id  = request.POST.get('object_id')

        author_id = extract_uuid_from_url(author_id) or author_id

        actor_id = request.POST.get('actor_id')
        actor = get_author(actor_id, create_remote=True)
        object = get_author(request.POST.get('object_id'))
        print("actor:", actor_id)
        inbox_item = Inbox.objects.filter(inbox_id=inbox_item_id).first()

        if actor is None:
            item = json.loads(inbox_item.inbox_item)
            follower = item.get("actor")
            RemoteFollow.objects.create(
                author=object, 
                follower_inbox= follower.get("host") + "authors/" + str(actor_id) + "/inbox/"
            )
            inbox_item.delete()

            return HttpResponseRedirect(reverse('mysocial:inbox', args=[author_id]))

        try:
            print("show", actor, object)
            follow_request = FollowRequest.objects.filter(actor=actor, object=object).first()

            if action == "approve":
                Follower.objects.create(author=follow_request.object, follower=follow_request.actor)
                
            inbox_item.delete()
            follow_request.delete()

            return HttpResponseRedirect(reverse('mysocial:inbox', args=[author_id]))

        except FollowRequest.DoesNotExist:
            return HttpResponseRedirect(reverse('mysocial:inbox', args=[author_id]))

    return HttpResponseRedirect(reverse('mysocial:inbox', args=[author_id]))

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
        return Response({"type": "authors", "items": serializer.data})

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
            followers = Follower.objects.filter(author__authorId=authorId)
            serializer = FollowerSerializer(followers, many=True)
            response_data = {"type": "followers", "items": [item['follower'] for item in serializer.data]}
            return Response(response_data)
        else:
            return Response({"type": "followers", "items": []})
    
class FollowDetail(APIView):
    def get_author(self, authorId):
        try:
            return Author.objects.get(authorId=authorId)
        except Author.DoesNotExist:
            raise Http404("Author not found")

    def get_follower(self, authorId, foreignAuthorUrl):
        try:
            return Follower.objects.get(author__authorId=authorId, follower__authorId=foreignAuthorUrl)
        except Follower.DoesNotExist:
            raise Http404("Follower not found")
    
    def get(self, request, authorId, foreignAuthorId, format=None): 
        try:
            foreignAuthor = self.get_author(foreignAuthorId)
            author = self.get_author(authorId)
            self.get_follower(authorId, foreignAuthorId)

            actor_serializer = AuthorSerializer(foreignAuthor)
            object_serializer = AuthorSerializer(author)

            follow_data = {
                "type": "Follow",
                "summary": f"{actor_serializer.data['displayName']} follows {object_serializer.data['displayName']}",
                "actor": actor_serializer.data,
                "object": object_serializer.data
            }
            return Response(follow_data)
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, authorId, foreignAuthorId, format=None):
        try:
            follower_instance = self.get_follower(authorId, foreignAuthorId)
            follower_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def put(self, request, authorId, foreignAuthorId, format=None):
        try:
            author = self.get_author(authorId)
            try:
                foreignAuthor = Author.objects.get(authorId=foreignAuthorId)
            except Author.DoesNotExist:
                return Response({"detail": "Foreign author not found."}, status=status.HTTP_404_NOT_FOUND)

            _, created = Follower.objects.get_or_create(author=author, follower=foreignAuthor)

            if created:
                return Response(status=status.HTTP_201_CREATED)
            else:
                return Response(status=status.HTTP_200_OK)

        except Http404:
            return Response({"detail": "Author not found."}, status=status.HTTP_404_NOT_FOUND)
    
    
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
    follow_requested = False
    viewing_own_profile = False
    viewing_friend_profile = False

    if request.user.is_authenticated:
        try:
            user_author = request.user.author
            viewing_own_profile = user_author.authorId == author_uuid
            already_following = Follower.objects.filter(author=author, follower=user_author).exists()
            follow_requested = FollowRequest.objects.filter(actor=user_author, object=author).exists()
            print(already_following)

            if not viewing_own_profile:
                    viewing_friend_profile = user_author.is_friend(author)

        except Author.DoesNotExist:
            pass

    context = {
        'author': author,
        'posts': posts,
        'already_following': already_following,
        'follow_requested': follow_requested,
        'viewing_own_profile': viewing_own_profile,
        'viewing_friend_profile': viewing_friend_profile,
    }
    
    return render(request, 'base/mysocial/public_profile.html', context)


def edit_profile(request, author_id):
    author = get_object_or_404(Author, authorId=author_id)

    # Check if the request user is authenticated and matches the author
    if request.user.is_authenticated and request.user.author.authorId == author_id:

        if request.method == 'POST':
            new_display_name = request.POST.get('displayName')
            new_bio = request.POST.get('bio')
            new_profileImage = request.FILES.get('profileImage')
            
            # Update the display name
            author.displayName = new_display_name
            
            # Update the bio
            author.bio = new_bio
            
            # Update the profile image if provided
            if new_profileImage:
                author.profileImage = new_profileImage
            
            author.save()
            return redirect('mysocial:public_profile', author_id=author_id)

        return render(request, 'base/mysocial/edit_profile.html', {'author': author})

    else:
        return HttpResponse('Unauthorized Access', status=401)

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

class PostImageView(View):
    def get(self, request, authorId, post_id):
        post = get_object_or_404(Post, postId=post_id, author__authorId=authorId)

        if post.type == 'IMAGE' and post.content:
            if post.visibility != 'PUBLIC' and (not request.user.is_authenticated or request.user.author != post.author):
                return HttpResponse('Unauthorized', status=401)
            try:
                format, imgstr = post.content.split(';base64,')
                ext = format.split('/')[-1] 
                image_data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                response = HttpResponse(image_data, content_type='image/' + ext)
                return response
            except ValueError:
                raise Http404("The image data is not in the correct format.")
        else:
            raise Http404("The requested post is not an image or doesn't exist.")


def display_stream(request, authorId):
    template_name = 'base/mysocial/stream_posts.html'
    action = request.GET.get('action', 'all') 
    author = get_object_or_404(Author, authorId=authorId)
    posts = Post.objects.exclude(visibility='UNLISTED').order_by('-published')
    visible_posts = []

    # if action == 'friends':
    #     # Get IDs of friends (both following and followers to consider mutual friendships)
    #     friends_ids = author.get_mutual_follows()
    #     mutual_follows_ids = [author.authorId for author in friends_ids]

    #     # Include the author's own posts in the stream as well
    #     visible_posts = posts.filter(author__authorId__in=friends_ids) | posts.filter(author=author)
        
    # else:  # Default action 'all', excluding 'UNLISTED' as per the initial queryset
    #     visible_posts = posts


    if action == 'all':

        # Filter posts based on visibility for the current user
        visible_posts = []
        for post in posts:
            if post.visibility == 'PUBLIC':
                visible_posts.append(post)
            elif post.visibility == 'PRIVATE':
                if author.is_friend(post.author) or author == post.author:
                    visible_posts.append(post)

    elif action == 'friends':

        # Filter posts based on visibility for the current user
        visible_posts = []
        for post in posts:
            if post.visibility == 'PRIVATE':
                if author.is_friend(post.author) or author == post.author:
                    visible_posts.append(post)

        visible_posts = [post for post in posts if author.is_friend(post.author) ]
    
    context = {
        'posts': visible_posts,
        'author': author,
    }
    return render(request, template_name, context)

class PostListCreateView(View):
    def get(self, request, authorId):
        author = get_object_or_404(Author, authorId=authorId)
        posts = Post.objects.filter(author=author).order_by('-published')

        # Filter based on the authentication status and relationship to the author
        if request.user.is_authenticated:
            if request.user.author == author:
                # Authenticated as author
                visible_posts = posts
            else:
                # Authenticated, but not as the author
                visible_posts = posts.filter(visibility='PUBLIC') | posts.filter(author__followers__follower=request.user.author, visibility='FRIENDS')
        else:
            # Not authenticated
            visible_posts = posts.filter(visibility='PUBLIC')

        # Serialize the posts
        serializer = PostSerializer(visible_posts, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, authorId):
        if not request.user.is_authenticated or request.user.author.authorId != authorId:
            return HttpResponse('Unauthorized', status=401)

        data = json.loads(request.body)
        data['author'] = authorId  

        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            post = serializer.save()
            return JsonResponse(serializer.data, status=201) 
        else:
            return JsonResponse(serializer.errors, status=400)
        
def encode_image_to_base64(image):
    image_content = image.read()
    # Encode image content to base64
    image_base64 = base64.b64encode(image_content).decode('utf-8')
    missing_padding = len(image_base64) % 4
    if missing_padding != 0:
        image_base64 += '=' * (4 - missing_padding)
    return image_base64

def create_post(request, authorId):
    template_name = 'base/mysocial/stream_posts.html'
    post_id = request.POST.get('post_id')
    title = request.POST.get('title')
    description = request.POST.get('description')
    content = request.POST.get('content')
    visibility = request.POST.get('visibility')
    image = request.FILES.get('image')
    content_type = "text/plain"
#        post_type = request.POST.get('type') 
    author = get_object_or_404(Author, authorId=authorId)
    markup = request.POST.get('markup', '') == 'on'

#        if post_type == 'IMAGE':
#            image = request.FILES.get('image')
    
    if markup:
        parser = commonmark.Parser()
        renderer = commonmark.HtmlRenderer()
        ast = parser.parse(content)
        content = renderer.render(ast)

    if post_id:
        # Update existing post
        post = get_object_or_404(Post, postId=post_id)
        post.title = title
        post.description = description
        post.content = content
        post.visibility = visibility
        post.image = image
        post.save()
    else:
        # Create new post
        if image:
            extension = str(image).split(".")[1]
            if extension == "jpeg":
                content_type = "image/jpeg;base64"
                content = encode_image_to_base64(image)
            else:
                content_type = "image/png;base64"
                content = encode_image_to_base64(image)

        if title:
            new_post = Post.objects.create(title=title, description=description, content_type=content_type, content=content, author=author, visibility=visibility, image=image)
            post_url = reverse('mysocial:post_detail', kwargs={'authorId': authorId, 'post_id': new_post.postId})
            new_post.url = request.build_absolute_uri(post_url)
            new_post.origin = request.build_absolute_uri(post_url)
            new_post.save()
            
            inbox_item = {
                "type": "post",
                "title": new_post.title,
                "id": str(new_post.postId),
                "source": new_post.source,
                "origin": new_post.origin,
                "description": new_post.description or "",
                "contentType": content_type,  
                "content": content,
                "author": {
                    "type": "author",
                    "id": str(author.authorId),
                    "host": request.get_host(),
                    "displayName": author.displayName,
                    "url": author.url,  
                    "github": author.github,  
                    "profileImage": author.profileImage.url if author.profileImage else None
                },
                "comments": new_post.url + "/comments", 
                "published": new_post.published.isoformat(),
                "visibility": new_post.visibility
            }
            
            remote_followers = RemoteFollow.objects.filter(author=author)
            for relation in remote_followers:
                inbox_url = relation.follower_inbox
                print(inbox_url)
                response = requests.post(f'{inbox_url}', json=inbox_item)
            
            
            followers = Follower.objects.filter(author=author)
            for relation in followers:
               Inbox.objects.create(
                  author=relation.follower,
                  inbox_item=json.dumps(inbox_item)
               )
               
        else:
            posts = Post.objects.all().order_by('-published')
            context = {
                'posts': posts,
                'author': author,
                'error_message': 'Please fill out all the information required',
            }
            return render(request, template_name, context)

    # Redirect to the posts list to see changes
    return redirect(reverse('mysocial:posts_by_author', kwargs={'authorId': authorId}))

class PostDetailView(APIView):
    def get(self, request, authorId, post_id):
        post = get_object_or_404(Post, postId=post_id)
        author = get_object_or_404(Author, authorId=authorId)
        comments = Comment.objects.filter(post=post).order_by('-published')

        if post.visibility == 'PUBLIC' or (post.visibility == 'PRIVATE' and author.is_friend(post.author) or author == post.author):
        
            post_data = {
                "type": "post",
                "title": post.title,
                "id": post.url,
                "source": post.source,
                "origin": post.origin,
                "description": post.description,
                "contentType": post.content_type,
                "content": post.content,
                "author": {
                    "type": "author",
                    "id": str(post.author.authorId),
                    "host": post.author.host,
                    "displayName": post.author.displayName,
                    "url": post.author.url,
                    "github": post.author.github,
                    "profileImage": post.author.profileImage.url if post.author.profileImage else None
                },
                "count": post.count,
                "comments": post.url + "comments/",
                "published": post.published.isoformat(),
                "visibility": post.visibility
            }

            return Response(post_data)
        else:
            return HttpResponse('Forbidden', status=403)

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
        
        author_data = AuthorSerializer(user_author).data

        inbox_item = {
            "summary": f"{user_author.displayName} Likes your post '{post.title}'",
            "type": "Like",
            "author": author_data,
            "object": post.url
        }

        Inbox.objects.create(
            author=post.author,
            inbox_item=json.dumps(inbox_item)
        )
    else:
        existing.delete()
        post.likesCount -= 1
        post.save()

    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return HttpResponseRedirect(referer_url)
    else:
        return HttpResponseRedirect('/')

@login_required
@require_POST
def share_post(request, post_id):

    post = get_object_or_404(Post, postId=post_id)
    author = get_object_or_404(Author, authorId=request.user.author.authorId)
    new_postId = uuid.uuid4()
    post_url = reverse('mysocial:post_detail', kwargs={'authorId': request.user.author.authorId, 'post_id': new_postId})
    stringpostId = str(post.postId)

    new_post = Post.objects.create(
        type=post.type,
        title=post.title,
        postId=new_postId,
        url=request.build_absolute_uri(post_url),
        source=post.origin,
        origin=request.build_absolute_uri(post_url),
        description=post.description,
        content_type=post.content_type,
        content=post.content,
        author=request.user.author,  # Change the author to the current user
        count=post.count,
        likesCount=post.likesCount,
        comments=post.comments,
        published=post.published,
        visibility=post.visibility,
        image = post.image,
    )

    inbox_item = {
        "type": "post",
        "title": post.title,
        "id": stringpostId,
        "source": post.source,
        "origin": post.origin,
        "description": post.description or "",
        "contentType": post.content_type,  
        "content": post.content,
        "author": {
            "type": "author",
            "id": str(post.author.authorId),
            "host": request.get_host(),
            "displayName": post.author.displayName,
            "url": post.author.url,  
            "github": post.author.github,  
            "profileImage": post.author.profileImage.url if post.author.profileImage else None
        },
        "comments": post.url + "/comments", 
        "published": post.published.isoformat(),
        "visibility": post.visibility
    }

    remote_followers = RemoteFollow.objects.filter(author=author)
    for relation in remote_followers:
        inbox_url = relation.follower_inbox
        print(inbox_url)
        response = requests.post(f'{inbox_url}', json=inbox_item)
            
            
    followers = Follower.objects.filter(author=author)
    for relation in followers:
        Inbox.objects.create(
            author=relation.follower,
            inbox_item=json.dumps(inbox_item)
        )
    
    referer_url = request.META.get('HTTP_REFERER')
    if referer_url:
        return HttpResponseRedirect(referer_url)
    else:
        return HttpResponseRedirect('/')
    
@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, postId=post_id, author=request.user.author)
    post.delete()
    return redirect(reverse('mysocial:posts_by_author', kwargs={'authorId': request.user.author.authorId}))

    
def fetch_github_activity(request, author_id):
    try:
        # Retrieve the Author instance from the database
        author = Author.objects.get(authorId=author_id)
        
        # Ensure the author has a linked GitHub username
        if not author.github:
            return render(request, 'base/mysocial/error_page.html', {'error': 'GitHub username not set for author.'})
        
        parsed_url = urlparse(author.github)  # Parse the URL
        path_parts = parsed_url.path.split('/')  # Split the path by '/'
        github_username = path_parts[-1] if path_parts[-1] else path_parts[-2]

        # GitHub API endpoint to fetch public events for a user
        github_events_url = f'https://api.github.com/users/{github_username}/events/public'
        response = requests.get(github_events_url)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
        
        # Process GitHub events and create post
        created_posts = []
        for event in response.json():
            title = event.get('type') + " Event"
            description = "GitHub event processed."
            content = event.get('payload', {}).get('commits', [{}])[0].get('message', 'No commit message available.')
            visibility = "PUBLIC" 
            
            # Create new post
            new_post = Post.objects.create(
                title=title,
                description=description,
                content=content,
                author=author,
                visibility=visibility,
            )
            
            # Generate post URL
            post_url = reverse('mysocial:post_detail', kwargs={'authorId': author_id, 'post_id': new_post.postId})
            new_post.url = request.build_absolute_uri(post_url)
            new_post.origin = request.build_absolute_uri(post_url)
            new_post.save()
            created_posts.append(new_post)
        return render(request, 'base/mysocial/github_posts.html', {'posts': created_posts, 'author': author})


    except Author.DoesNotExist:
        return render(request, 'base/mysocial/error_page.html', {'error': 'Author not found.'})
    except requests.HTTPError as e:
        return render(request, 'base/mysocial/error_page.html', {'error': str(e)})



@login_required
def comments_post(request, authorId, post_id):
    post = get_object_or_404(Post, postId=post_id)
    
    if request.method == 'GET':
        comments = Comment.objects.filter(post=post).order_by('-published')
        comments_data = [{
            "type": "comment",
            "author": {
                "id": str(comment.author.authorId),
                "displayName": comment.author.displayName,
                "profileImage": comment.author.profileImage.url if comment.author.profileImage else None,
            },
            "comment": comment.comment,
            "contentType": comment.contentType,
            "published": comment.published.isoformat(),
            "id": str(comment.commentId),
        } for comment in comments]

        return JsonResponse({
            "type": "comments",
            "comments": comments_data,
        })
    
    if request.method == 'POST':
        comment_content = request.POST.get('comment')

        if not comment_content.strip():
            return redirect('mysocial:post_detail', authorId=authorId, post_id=post_id)

        new_comment = Comment.objects.create(
            author=request.user.author, 
            post=post,
            comment=comment_content,
            contentType='text/plain',
        )

        author_data = AuthorSerializer(request.user.author).data

        inbox_item = {
            "type": "comment",
            "author": author_data,
            "comment": new_comment.comment,
            "contentType": new_comment.contentType,
            "published": new_comment.published.isoformat(),
            "id": str(new_comment.commentId)
        }

        Inbox.objects.create(
            author=post.author,
            inbox_item=json.dumps(inbox_item)
        )

        return redirect('mysocial:post_detail', authorId=authorId, post_id=post_id)
    
    return HttpResponse(status=405)


class LikedView(APIView):
    def get_author(self, authorId):
        try:
            return Author.objects.get(authorId=authorId)
        except Author.DoesNotExist:
            raise Http404("Author not found")

    def get(self, request, authorId, format=None):
        author = self.get_author(authorId)
        likes = Like.objects.filter(author=author).order_by('-timestamp') 

        liked_items = []
        for like in likes:
            author_serializer = AuthorSerializer(author)

            liked_item = {
                "summary": f"{author.displayName} Likes your post",
                "type": like.type,
                "author": author_serializer.data,
                "object": like.object_url
            }
            liked_items.append(liked_item)

        response_data = {
            "type": "liked",
            "items": liked_items
        }

        return Response(response_data)
    
    
def send_remote_follow(request):
    if request.method == 'POST':
        object_id = request.POST.get('object_id')
        node_id = request.POST.get('node_id')
        
        author_serializer = AuthorSerializer(request.user.author)
        data = {
            "type": "Follow",
            "summary": f"{request.user.username} wants to follow {request.POST.get('object_displayName')}",
            "actor": author_serializer.data
            #{
                #"type": "author",
                #"id": int(request.user.author.authorId),
                #"host": request.user.author.host,
                #"displayName": request.user.author.displayName,
                #"url": request.user.author.url,
                #"github": request.user.author.github,
                #"profileImage": request.user.author.profileImage,
            #}
            ,
            "object": {
                "type": "author",
                "id": object_id,
                "host": request.POST.get('object_host'),
                "displayName": request.POST.get('object_displayName'),
                "url": request.POST.get('object_url'),
                "github": request.POST.get('object_github'),
                "profileImage": request.POST.get('object_profileImage'),
            }
        }
        node = Node.objects.get(node_id=node_id)
        
        response = requests.post(f"{object_id}/inbox/", json=data, auth=HTTPBasicAuth(node.username, node.password))
        
        if response.status_code == 201:
            return JsonResponse({'message': 'Follow request sent successfully.'}, status=201)
        else:
            return JsonResponse({'message': 'Failed to send follow request.', 'error': response.text}, status=response.status_code)

    return JsonResponse({'message': 'Invalid request method. Only POST is allowed.'}, status=405)

def friends_list(request, author_id):
    author = get_object_or_404(Author, authorId=author_id)

    friends = author.get_mutual_follows()

    # Followers
    followers = author.get_followers()

    # Following
    following = author.get_following()

    context = {
        'author': author,
        'friends': friends,
        'followers': followers,
        'following': following,
    }

    return render(request, 'base/mysocial/friends_list.html', context)

@login_required
def display_post(request, authorId, post_id):
    post = get_object_or_404(Post, postId=post_id)
    comments = Comment.objects.filter(post=post).order_by('-published')
    author = request.user.author

    if post.visibility == 'PRIVATE':
        if post.author != author:
            mutual_follows = author.get_mutual_follows()

            if post.author not in mutual_follows:
                raise Http404("You do not have permission to view this post.")
            
    context = {'post': post, 'author': post.author, 'comments': comments}
    
    return render(request, 'base/mysocial/post_detail.html', context)
