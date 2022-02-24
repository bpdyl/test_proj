from django.db import models
from django.contrib.auth.models import User,Group
from django.db.models import Count
# Create your models here.
class FriendRequest(models.Model):
	"""
	A friend request consists of two main parts:
		1. SENDER
			- Person sending/initiating the friend request
		2. RECIVER
			- Person receiving the friend friend
	"""

	sender 				= models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
	receiver 			= models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver")

	is_pending			= models.BooleanField(blank=False, null=False, default=True)

	timestamp 			= models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.sender.username

	def accept_request(self):
		receiver_friend_list = FriendList.objects.get(user = self.receiver)
		if receiver_friend_list:
			receiver_friend_list.add_friend(self.sender)
			sender_friend_list = FriendList.objects.get(user = self.sender)
			if sender_friend_list:
				sender_friend_list.add_friend(self.receiver)
				self.is_pending = False
				self.save()

	def decline_request(self):
		self.is_pending = False
		self.save()

	def cancel_request_by_sender(self):
		self.is_pending = False
		self.save()


class FriendList(models.Model):
    user = models.OneToOneField(User,on_delete = models.CASCADE,related_name='user')
    friends = models.ManyToManyField(User, blank=True, related_name='friends')

    def __str__(self):
        return self.user.username

    def add_friend(self, other_user):
        try:
            self.friends.add(other_user)
        except:
            raise ValueError
        # if not other_user in self.friends.all():
        #     self.friends.add(other_user)
        #     self.save()
    
    def remove_friend(self, other_user):
            self.friends.remove(other_user)
            '''
            logic for Deactivating the private chat between the removed friend users
            '''

    def unfriend(self, user_to_be_removed):
        remover_friends_list = self
        #Remove garne manche ko friend list bata friend lai remove garne
        remover_friends_list.remove_friend(user_to_be_removed)
        #jaslai remove gariyeko cha tesko bata ni unfriend garauna parcha
        friends_list = FriendList.objects.get(user = user_to_be_removed)#to be removed user ko friend list
        friends_list.remove_friend(remover_friends_list.user)

    def is_mutual_friend(self, friend):
        if friend in self.friends.all():
            return True
        else:
            return False

class TrackingModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now = True)

	class Meta:
		abstract = True



class ThreadManager(models.Manager):
    def get_or_create_personal_thread(self, user1, user2):
        threads = self.get_queryset().filter(thread_type='personal')
        threads = threads.filter(users__in=[user1, user2]).distinct()
        threads = threads.annotate(u_count=Count('users')).filter(u_count=2)
        if threads.exists():
            return threads.first()
        else:
            thread = self.create(thread_type='personal')
            thread.users.add(user1)
            thread.users.add(user2)
            return thread

    def by_user(self, user):
        return self.get_queryset().filter(users__in=[user])


class FriendRequestThread(TrackingModel):
	THREAD_TYPE =(
		('personal','Personal'),
		('group','Group')
		)
	name = models.CharField(max_length=50,null=True,blank=True)
	thread_type = models.CharField(max_length=15,choices =THREAD_TYPE,default='personal')
	users = models.ManyToManyField('auth.User')

	objects = ThreadManager()

	def __str__(self)->str:
		if self.thread_type=='personal' and self.users.count() == 2:
			return f'{self.users.first()} and {self.users.last()}'
		return f'{self.name}'

class PrivateChatManager(models.Manager):
    def create_room_if_none(self,user1,user2):
        chat_thread = PrivateChatThread.objects.filter(Q(first_user = user1, second_user = user2) | 
        Q(first_user = user2, second_user = user1)
        ).first()
        if not chat_thread:
            print("not found private chat")
            chat_thread = PrivateChatThread.objects.create(first_user = user1, second_user = user2)
            chat_thread.save()
        return chat_thread

    # def by_user(self, **kwargs):
    #     user = kwargs.get('user')
    #     lookup = Q(first_user = user) | Q(second_user = user)
    #     qs = self.get_queryset().filter(lookup).distinct()
    #     return qs

class PrivateChatThread(models.Model):
    first_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='thread_first_person')
    second_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,blank=True,related_name='other_user')
    connected_users = models.ManyToManyField(User,blank = True, related_name="private_connected_users")
    is_active = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    objects = PrivateChatManager()
    class Meta:
        unique_together = ['first_user','second_user']

    def __str__(self) -> str:
        return f'chat thread {self.first_user} {self.second_user}'
    def get_connected_users(self):
        return " , ".join([str(p) for p in self.connected_users.all()])

    def connect(self,user):
        is_added = False
        if not user in self.connected_users.all():
            self.connected_users.add(user)
            is_added = True
            print("ok added")
        return is_added

    def disconnect(self,user):
        is_removed = False
        if user in self.connected_users.all():
            self.connected_users.remove(user)
            is_removed = True
            print("ok removed")
        return is_removed
    
    def last_msg(self):
        return self.private_thread.all().last()


class PrivateChatMessageManager(models.Manager):
    def by_private_thread(self, private_thread):
        print(private_thread)
        qs = PrivateChatMessage.objects.filter(chat_thread=private_thread).order_by('-timestamp')
        print(qs)
        return qs

class PrivateChatMessage(models.Model):
    chat_thread = models.ForeignKey(PrivateChatThread, null=True,blank=True, on_delete=models.CASCADE,related_name="private_thread")
    sender= models.ForeignKey(User, on_delete=models.CASCADE,related_name='msg_sender')
    message_content = models.TextField(unique=False,blank=False,null=True) 
    message_type = models.CharField(max_length=50,null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = PrivateChatMessageManager()



class GroupChatThread(Group):
    group_name = models.CharField(max_length=100,null=True)
    admin = models.ForeignKey(User,null=True, on_delete=models.SET_NULL, related_name ='grpadmin')
    image = models.ImageField(default='group_photos/nouser.jpg',upload_to='group_photos')
    group_description = models.TextField(blank=True, help_text="description of the group")
    created_at = models.DateTimeField(auto_now_add=True,auto_now=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.group_name

    @property
    def gc_name(self):
        return "GroupChat-%s" % self.id


class GroupChatMessageManager:
    def by_gc_thread(self, gc_thread):
        qs = GroupChatMessage.objects.filter(gc_thread=gc_thread).order_by("-timestamp")
        return qs

class GroupChatMessage(models.Model):
    gc_thread = models.ForeignKey(GroupChatThread,on_delete=models.CASCADE, related_name='group_message')
    sender = models.ForeignKey(User,on_delete=models.CASCADE,related_name='grp_sender')
    timestamp = models.DateTimeField(auto_now_add=True)
    message_type = models.CharField(max_length=50, blank=True, null= True, default='text')
    content = models.TextField(unique=False,blank=False)

    objects = GroupChatMessageManager()

    def __str__(self):
        return self.content + self.sender.username