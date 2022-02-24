from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import FriendRequestThread
from asgiref.sync import async_to_sync, sync_to_async
import json

class ButtonConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		self.room_name = self.scope['url_route']['kwargs']['room_name']
		self.room_group_name = 'friend_request_%s' % self.room_name

		#Join room group
		await self.channel_layer.group_add(
			self.room_group_name,
			self.channel_name
			)
		await self.accept()
		print("button conusmer connect vo")
		
	async def disconnect(self,close_code):
		await self.channel_layer.group_discard(
				self.room_group_name,
				self.channel_name
			)
	#Receive message from websocket 	
	async def receive(self,text_data):
		print('>>>',text_data)
		text_data_json = json.loads(text_data)
		message = text_data_json['message']

		print("ist me "+str(message))
		await self.channel_layer.group_send(
			self.room_group_name,{
			'type':'chat_message',
			'message':message
			}
			)
	#receive message from room group
	async def friend_request(self,event):
		content = event['content']
		print("its me content"+content)
		#Send message to websocket
		await self.send(text_data=content)




class UIConsumer(AsyncWebsocketConsumer):
	async def connect(self):
		
		me=self.scope['user']
		other_username = self.scope['url_route']['kwargs']['username']
		other_user =await sync_to_async(User.objects.get)(username = other_username) 
		thread_obj = await sync_to_async(FriendRequestThread.objects.get_or_create_personal_thread)(me,other_user)
		self.room_name = thread_obj.id
		print("request room is ",self.room_name)
		self.room_group_name = 'ui_update_%s' % self.room_name
		#Join room group
		await self.channel_layer.group_add(
			self.room_group_name,
			self.channel_name
			)
		
		await self.accept()
		print("Ui consumer")
	async def disconnect(self,close_code):
		await self.channel_layer.group_discard(
				self.room_group_name,
				self.channel_name
			)
	async def receive(self,text_data):
		print('>>>',text_data)
		text_data_json = json.loads(text_data)
		message = text_data_json['message']

		print("ist me "+str(message))
		await self.channel_layer.group_send(
			self.room_group_name,{
			'type':'my_req_update',
			'message':message
			}
			)
	async def my_req_update(self,event):
		content = event['content']
		print("its me UI ko content "+content)
		await self.send(text_data=content)