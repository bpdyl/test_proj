from .models import *
from rest_framework import serializers
from itertools import chain
from django.contrib.auth.models import User,Group
from django.core import serializers as core_serializers

class GroupChatThreadSerializer(serializers.ModelSerializer):
		class Meta:
			model = GroupChatThread
			fields ='__all__'

class GroupSerializer(serializers.ModelSerializer):
	class Meta:
		model = Group
		fields = '__all__'
class UserSerializer(serializers.ModelSerializer):
	# groups = GroupSerializer(many=True)
	class Meta:
		model = User
		fields = '__all__'


class PrivateChatMessageSerializer(serializers.ModelSerializer):
	sender = UserSerializer()
	class Meta:
		model = PrivateChatMessage
		fields = '__all__'

class PrivateChatThreadSerializer(serializers.ModelSerializer):
	first_user = UserSerializer()
	second_user = UserSerializer()
	last_message = serializers.SerializerMethodField(read_only = True)
	class Meta:
		model = PrivateChatThread
		fields = '__all__'
		fields = ('id','last_message','second_user','first_user','updated_at','is_active',)
		# fields =('id','first_user','second_user','is_active','updated_at',)

	def get_last_message(self,obj):
		msg = obj.last_msg()
		print("this is msg",msg)
		serializer = PrivateChatMessageSerializer(msg)
		print("this is ",serializer)
		return serializer.data

# class ThreadSerializer(serializers.Serializer):
# 	private_threads = PrivateChatThreadSerializer(many = True)
# 	group_threads = GroupChatThreadSerializer(many = True)
# 	chat_threads = chain(private_threads,group_threads)
# 	print("my chat threads",chat_threads)