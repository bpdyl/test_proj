from django.shortcuts import render, HttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import FriendRequest,FriendList
from .utils import FriendRequestStatus, get_friend_request_or_false
from django.http.response import JsonResponse
from .models import FriendRequestThread,FriendList,GroupChatThread,PrivateChatThread
import json
from datetime import datetime
from itertools import chain
from operator import attrgetter
from django.forms.models import model_to_dict
from .decorators import render_to
from rest_framework.response import Response
from .serializers import *
from rest_framework import viewsets
# Create your views here.
def index(request,*args,**kwargs):
	if request.method == "GET":
		current_user = request.user
		thread_id = request.GET.get('thread_id')
		context = {}
		context['current_user'] = current_user
		if thread_id:
			private_thread = PrivateChatThread.objects.get(pk=thread_id)
			context['private_thread'] = private_thread
		threads1 = PrivateChatThread.objects.filter(first_user = current_user,is_active=True)
		threads2 = PrivateChatThread.objects.filter(second_user= current_user, is_active=True)

		group_ids = request.user.groups.values_list('id')
		group_threads = GroupChatThread.objects.filter(id__in = group_ids)
		threads = sorted(chain(threads1,threads2,group_threads),key = attrgetter('updated_at'),reverse = True)

		for f in threads:
			if f is GroupChatThread:
				print("group")
			if hasattr(f,'first_user') or hasattr(f,'second_user'):
				if f.first_user == current_user:
					print("second user",f.second_user)
					print(f.private_thread.last())
				else:
					print("first_user",f.first_user)
					print(f.private_thread.last().message_content)
			else:
				print(f)
				print("image",f.image)
				print(f.group_message.all())
		print("this is list of threads",threads)
		context['threads'] = threads
		return render(request,'index.html',{
			'room_name':current_user.username,
			'room_id':current_user.id,
			'threads':threads,
			})

@render_to('index.html')
def user_list_update(request,*args,**kwargs):
	current_user = request.user
	threads1 = PrivateChatThread.objects.filter(first_user = current_user,is_active=True)
	threads2 = PrivateChatThread.objects.filter(second_user= current_user, is_active=True)

	group_ids = request.user.groups.values_list('id')
	group_threads = GroupChatThread.objects.filter(id__in = group_ids).only('id','group_name','admin','group_description','updated_at')
	group_t = GroupChatThread.objects.filter(id__in = group_ids)
	print(str(group_threads.query))
	print(group_threads)
	for f in group_threads:
		print(f.image.url)
	print(group_t)
	threads = sorted(chain(threads1,threads2,group_threads),key = attrgetter('updated_at'),reverse = True)
	threads_dict = [model_to_dict(t) for t in threads]
	print("this is threads dict",threads_dict)
	threads_list = json.dumps({'mythreads':threads_dict})
	return HttpResponse(threads_list)

def perform(data):
	print("yo ma "+str(data))
	uname = data['username']
	uid = data['user_id']
	print(uname)
	print("yo chai room name friend_request_"+str(uname))
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		"friend_request_"+str(uname),
		{
			'type': 'friend_request',
			'content':json.dumps(data),
		}
	)

def ui_update(data):
	uid = data['user_id']
	thread_id = data['thread_id']
	print("yo chai room name ui_update"+str(thread_id))
	channel_layer = get_channel_layer()
	async_to_sync(channel_layer.group_send)(
		"ui_update_"+str(thread_id),
		{
		'type': 'my_req_update',
		'content':json.dumps(data),
		}
	)

def test(request):
	
	return HttpResponse("Done")

REQUEST_SUCCESS = "Friend request has been sent."
ERROR = "Something went wrong."
NO_USER_ID = "Unable to perform action. User id not available."
ALREADY_SENT = "You have already sent the request."
NOTHING_TO_CANCEL = "Nothing to cancel. Request doesnot exist."
REQUEST_CANCEL = "Friend request cancelled."

@login_required
def send_request(request):
	print("i got hit")
	current_user = request.user
	data = {}

	if request.method == 'POST':
		print("hello world")
		user_id = request.POST.get("receiver_user_id")
		print("request aayo hai"+str(user_id))
		if user_id:
			receiver = User.objects.get(pk = user_id)
			data['username'] = receiver.username
			data['user_id']=receiver.id
			try:
				friend_request_if_any = FriendRequest.objects.get(sender = current_user, receiver = receiver)
				print("vetiyo "+str(friend_request_if_any))
				if friend_request_if_any.is_pending:
					print("Cha ta pahilai")
					data['result'] = ALREADY_SENT
					return JsonResponse(data)
				friend_request_if_any.is_pending = True
				friend_request_if_any.save()
				data['result'] = REQUEST_SUCCESS
			except FriendRequest.DoesNotExist:
				print(" aba banauchu")
				friend_request = FriendRequest(sender = current_user, receiver = receiver)
				friend_request.save()
				data['result'] = REQUEST_SUCCESS
			if data['result'] == None:
				data['result'] = ERROR
		else:
			data['result'] = NO_USER_ID
	# channel_layer = get_channel_layer()
	# print(channel_layer)
	# async_to_sync(channel_layer.group_send)(
	# 	"friend_request_broadcast",
	# 	{
	# 		'type': 'friend_request',
	# 		'message':"data"
	# 	}
	# )
	thread_obj = FriendRequestThread.objects.get_or_create_personal_thread(current_user,receiver)
	print("This is send wala thread obj"+str(thread_obj))
	data['thread_id'] = thread_obj.id
	thread_user = list(thread_obj.users.all().values('username'))
	print(thread_user)
	data['connected_users'] = thread_user
	perform(data)
	ui_update(data)
	return JsonResponse(data)

@login_required
def cancel_request(request):
    current_user = request.user
    data = {}
    if request.is_ajax():
        user_id = request.POST.get("receiver_user_id")
        print("cancel request" + str(user_id))
        if user_id:
            receiver = User.objects.get(pk = user_id)
            data['username'] = receiver.username
            data['user_id']=receiver.id

            print("yo cancel gardim hai ta")
            try:
                friend_requests = FriendRequest.objects.get(sender = current_user, receiver = receiver, is_pending =True)
                friend_requests.cancel_request_by_sender()
                data['result'] = REQUEST_CANCEL
            except FriendRequest.DoesNotExist:
                data['result'] = NOTHING_TO_CANCEL
        else:
            data['result'] = NO_USER_ID
    thread_obj = FriendRequestThread.objects.get_or_create_personal_thread(current_user,receiver)
    print("This is thread object"+str(thread_obj))
    data['thread_id'] = thread_obj.id
    thread_user = list(thread_obj.users.all())
    print(thread_user)
    perform(data)
    ui_update(data)
    return JsonResponse(data)

def view_profile(request, *args, **kwargs):
    context = {}
    user_id = kwargs.get("userId")
    print("this is "+str(user_id))
    try:
        user_account = User.objects.get(pk = user_id)
        print(user_account.username)
    except:
        return HttpResponse("User Id doesnot exist")
    if user_account:
        context['user_account'] = user_account
        
        try:
            list_of_friends = FriendList.objects.get(user = user_account)
            print("yo chai ma "+str(list_of_friends))
        except FriendList.DoesNotExist:
            list_of_friends = FriendList(user = user_account)
            list_of_friends.save()
        user_friends = list_of_friends.friends.all()
        print("This is user_friends"+str(user_friends))
        context['user_friends'] = user_friends

        #Define variables for the template to check whether the profile is of self or friends or other users
        is_self = True
        is_friend = False
        friend_request_status = FriendRequestStatus.NO_REQUEST_SENT.value
        friend_requests = None
        current_user = request.user
        if current_user.is_authenticated and current_user != user_account:
            is_self = False
            if user_friends.filter(pk = current_user.id):
                is_friend = True
            else:
                is_friend = False
                incoming_request = get_friend_request_or_false(sender = user_account, receiver=current_user)
                outgoing_request = get_friend_request_or_false(sender = current_user, receiver = user_account)

                if  incoming_request!= False:
                    friend_request_status = FriendRequestStatus.INCOMING_REQUEST.value
                    context['pending_request_id'] = incoming_request.id
                elif outgoing_request != False:
                    friend_request_status = FriendRequestStatus.OUTGOING_REQUEST.value
                else:
                    friend_request_status = FriendRequestStatus.NO_REQUEST_SENT.value

        try:
            friend_requests = FriendRequest.objects.filter(receiver = current_user, is_pending = True)
        except:
            pass
        context['is_self'] = is_self
        context['is_friend'] = is_friend
        context['friend_request_status'] = friend_request_status
        context['friend_requests'] = friend_requests
        context['room_name'] = user_account.username
        context['room_id']=user_account.id

        return render(request,'profile.html',context)

from collections import namedtuple

Thread = namedtuple('Thread',('chat_threads'))



class ThreadViewSet(viewsets.ViewSet):
	def list(self,request):
		current_user = request.user
		threads1 = PrivateChatThread.objects.filter(first_user = current_user,is_active=True)
		threads2 = PrivateChatThread.objects.filter(second_user= current_user, is_active=True)
		combined_threads = list(chain(threads1,threads2))
		for f in combined_threads:
			print(f.first_user)
		group_ids = request.user.groups.values_list('id')
		group_threads = GroupChatThread.objects.filter(id__in = group_ids)
		private_serializer = PrivateChatThreadSerializer(combined_threads,many = True)
		group_serializer = GroupChatThreadSerializer(group_threads,many = True)
		# user_serializer = UserSerializer(chain(threads1,threads2),many = True)
		# print("this is user ",user_serializer.data)
		response = private_serializer.data + group_serializer.data

		chat_thread = sorted(response,key =lambda x: x['updated_at'],reverse = True)
		my_response ={}
		my_response['chat_threads'] = chat_thread
		# thread = Thread(
		# 		group_threads = group_threads,
		# 		private_threads = chain(threads1,threads2), 
		# 		chat_threads = my_threads,

		# )
		

		return Response(my_response)