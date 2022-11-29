from django.urls import path

from . import consumers
# to use path instead of re_path--> https://stackoverflow.com/a/54107211/9217577
websocket_urlpatterns = [
	path('', consumers.ChatConsumer.as_asgi()),
]
   # re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),

