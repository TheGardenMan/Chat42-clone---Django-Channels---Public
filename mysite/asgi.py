import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
# get_asgi_application should be called before doing any step while running daphne for nginx ..
# https://stackoverflow.com/a/64973001
django_asgi_app = get_asgi_application()

from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing
application = ProtocolTypeRouter({
	# If it's http,pass it to do the usual stuff ->urls.py-->views.py
  "http": django_asgi_app,
	# If it's websocket,pass to routing.py-->consumers.py
  "websocket":URLRouter(
            chat.routing.websocket_urlpatterns
    ),
})


