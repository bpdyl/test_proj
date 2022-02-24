from channels.routing import ProtocolTypeRouter,URLRouter
from channels.auth import AuthMiddlewareStack

from django.urls import path,re_path
from firstPage import consumers

websocket_urlPattern=[
	re_path(r'ws/friendrequest/(?P<room_name>\w+)/$',consumers.ButtonConsumer.as_asgi()),
	re_path(r'ws/uiupdate/(?P<username>\w+)/$',consumers.UIConsumer.as_asgi()),

]

application=ProtocolTypeRouter({
	# 'http':
	'websocket':AuthMiddlewareStack(URLRouter(websocket_urlPattern)),

	})