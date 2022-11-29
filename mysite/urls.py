from django.conf import settings
from django.contrib import admin
from django.views.generic import TemplateView
from django.urls import path
from chat import views
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path
from django.conf.urls.static import static

urlpatterns = [
	#pages
	path('',views.index),
    path('signup_page/',views.signup_page),
    path('login_page/',views.login_page),
    path('start_chat/',views.start_chat),
    path('chat/',views.chat),
	# auth
	path('signup/',views.UserCreate.as_view()),
	path('login/', obtain_auth_token),
	path('logout/', views.Logout.as_view()),
	# APIs
	#path('create_profile/',views.create_profile),
	path('set_preferences/',views.set_preferences),
	path('username_check/',views.username_check),
	path('get_preferences/',views.get_preferences),
	# Monitoring APIs: Admin only
	path('online_users/',views.online_users),
	path('new_matches/',views.new_matches),
	path('admin_view/',views.admin_view)

]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)