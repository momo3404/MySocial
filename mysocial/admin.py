from django.contrib import admin
from .models import *
from django.contrib.auth.models import User

# Register your models here.
admin.site.register(Post)
admin.site.register(Author)
admin.site.register(Node)
admin.site.register(Follower)
admin.site.register(FollowRequest)
admin.site.register(Like)

def make_active(modeladmin, request, queryset):
    queryset.update(is_active=True)

class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_active']
    ordering = ['username']
    actions = [make_active]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Inbox)
admin.site.register(RemoteFollow)
