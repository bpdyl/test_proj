from django.contrib import admin
from .models import FriendRequest,FriendList
from .models import FriendRequestThread,PrivateChatThread,GroupChatThread,GroupChatMessage,PrivateChatMessage

# Register your models here.
admin.site.register(FriendRequest)
admin.site.register(FriendList)
admin.site.register(FriendRequestThread)
admin.site.register(GroupChatThread)
admin.site.register(GroupChatMessage)
admin.site.register(PrivateChatMessage)
admin.site.register(PrivateChatThread)
