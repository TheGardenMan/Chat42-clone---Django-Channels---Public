from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.cache import cache_page

from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import permission_classes,api_view,renderer_classes

from .serializer import UserSerializer
from . import db_handle
from . import redis_handle

#exception handler for API views and html views
def exception_handler(func):
	# https://stackoverflow.com/a/64212552
	def inner_function(*args, **kwargs):
		# args is a tuple which contains the args passed to target function
		try:
			return func(*args, **kwargs)
		except Exception as e:
			print("\n@exception_handler: started")
			# if this function had a user,clean him
			if hasattr(args[0],'user'):
				user_id = args[0].user.id
			else:
				user_id = 0

			tb = e.__traceback__
			error_flow = "ERR: "
			# skip the first function since it is this inner_function
			tb = tb.tb_next
			while tb is not None:
				filename = tb.tb_frame.f_code.co_filename
				function_name = tb.tb_frame.f_code.co_name
				lineno = tb.tb_lineno
				error_flow = ''.join([error_flow,filename,":",str(lineno),":",function_name," ==> "])
				tb = tb.tb_next
			error_name = type(e).__name__
			error_message = str(e)
			print(f"user_id:{user_id} {error_name} \n{error_message} \n{error_flow}")
			db_handle.error_logger(user_id, error_name, error_message, error_flow)
			print("exception handling done...")
			#exception handler should return a httpresponse.otherwise internal server error will happen
			return HttpResponse("exception in server.handled", status=500)
	return inner_function

#check if given token in cookie is valid.used by views which serve HTML
def is_authenticated_cookie(token_key):
	try:
		token = Token.objects.get(key=token_key)
		#return token.user
		return 1
	except Exception as e:
		print("@is_authenticated_cookie:user is not logged in ", e)
		return -1

#.............................APIs.............................
# /signup
class UserCreate(APIView):
	@exception_handler
	def post(self, request, format='json'):
		temp_data=request.data.dict()
		temp_data['username']=temp_data['username'].lower()
		#check for all fields before creating the user
		if not 'gender' in temp_data or not 'birth_month' in temp_data or not 'birth_year' in temp_data:
			print("@usercreate class: gender or birth year or month is missing")
			return Response({"error":"required field missing"},status=status.HTTP_400_BAD_REQUEST)
		#todo: add validations here for allowed values of gender,birth_month,birth_year
		serializer = UserSerializer(data=temp_data)
		if serializer.is_valid():
			user = serializer.save()
			if user:		
				token = Token.objects.create(user=user)
				json = serializer.data
				json['token'] = token.key
				## this also sets default preferences in db_handle
				if db_handle.create_profile(user.id,request.data['gender'],request.data['birth_month'],request.data['birth_year'])==1:
					return Response(json, status=status.HTTP_201_CREATED)
				else:
					print(f"ERR: Profile creation failed for user {user.id}.DO: Cleanup this user")
		#if username is not unique or db_handle.create_profile fails, below line will be executed
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@exception_handler
def username_check(request):
	if db_handle.username_check(request.data["username"].lower())!=-1:
		return Response(status=status.HTTP_200_OK)
	return Response(status=status.HTTP_204_NO_CONTENT)

# /set_preferences
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer]) 
@exception_handler
def set_preferences(request):
	if db_handle.set_preferences(request.user.id,request.data['gender_preference'],request.data['bio'])!=-1:
		return Response(status=status.HTTP_200_OK)
	return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer]) 
@exception_handler
def get_preferences(request):
	result=db_handle.get_profile_and_preferences(request.user.id)
	if result!=-1:
		return Response(result,status=status.HTTP_200_OK)
	return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#......................HTML views........................
#entry point
@exception_handler
def index(request):
	token = request.COOKIES.get('token')
	# If no token
	if not token:
		# return HttpResponseRedirect(settings.SERVER_URL+"signup_page/")
		return HttpResponseRedirect("/signup_page/")
	# if given token is invalid
	if is_authenticated_cookie(request.COOKIES.get('token'))==-1:
		return HttpResponseRedirect("/signup_page/")
	return HttpResponseRedirect("/start_chat/")

@exception_handler
#Only render is cached. "errored" views aren't cached.
@cache_page(settings.CACHE_EXPIRE_SECONDS)
def signup_page(request):
	token = request.COOKIES.get('token')
	# If no token
	if not token:
		return render(request,"signup.html",{})
	# or token is invalid, serve the signup page as expected
	if is_authenticated_cookie(request.COOKIES.get('token'))==-1:
		return render(request,"signup.html",{})
	return HttpResponseRedirect("/start_chat/")

@exception_handler
#Only render is cached. "errored" views aren't cached.
@cache_page(settings.CACHE_EXPIRE_SECONDS)
def login_page(request):
	token = request.COOKIES.get('token')
	# If no token
	if not token:
		return render(request,"login.html",{})
	# or token is invalid, serve the login page as expected
	if is_authenticated_cookie(request.COOKIES.get('token'))==-1:
		return render(request,"login.html",{})
	return HttpResponseRedirect("/start_chat/")

# no need for exception handler here since this function is not standalone
def serve_page_if_authenticated(request,template_name):
	'''pass me the request and template name.If auth-ed,I will serve the template.else I will redirect to signup page'''
	token = request.COOKIES.get('token')
	# If no token
	if not token:
		return HttpResponseRedirect("/signup_page/")
	# if given token is invalid
	if is_authenticated_cookie(request.COOKIES.get('token'))==-1:
		return HttpResponseRedirect("/signup_page/")
	return render(request,template_name,{})

@exception_handler
#Only render is cached. "errored" views aren't cached.
@cache_page(settings.CACHE_EXPIRE_SECONDS)
def start_chat(request):
	return serve_page_if_authenticated(request,'start_chat.html')


def get_user(token_key):
	try:
		token = Token.objects.get(key=token_key)
		return token.user
	except Exception as e:
		print("Error at get_user ", e)
		return None

@exception_handler
#Only render is cached. "errored" views aren't cached.
@cache_page(settings.CACHE_EXPIRE_SECONDS)
def admin_view(request):
	if is_authenticated_cookie(request.COOKIES.get('token'))!=-1:
		# You can't "request.user.id" here since not using api_view(it returns a page for 404 so..) and this is not a WSGI server
		user = get_user(request.COOKIES.get('token'))
		if user.id==settings.ADMIN_USER_ID and user.username==settings.ADMIN_USERNAME:
			return render(request,"admin_view.html",{})
		else:
			print(f"CRITICAL \"{user.id}:{user.username}\" is trying to access admin_view page")
	# cant use Response here
	return HttpResponse(status=404)

@exception_handler
@cache_page(settings.CACHE_EXPIRE_SECONDS)
def chat(request):
	return serve_page_if_authenticated(request,'chat_old.html')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer]) 
@exception_handler
def online_users(request):
	# ToDo: write an isAdmin decorator
	if request.user.id==settings.ADMIN_USER_ID and request.user.username==settings.ADMIN_USERNAME:
		return Response({"count":redis_handle.get_online_users_count()},status=status.HTTP_200_OK)
	else:
		# CRITICAL
		print(f"CRITICAL \"{request.user.id}:{request.user.username}\" is trying to access users_online API")
	return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer]) 
@exception_handler
def new_matches(request):
	print(request)
	if request.user.id==settings.ADMIN_USER_ID and request.user.username==settings.ADMIN_USERNAME:
		match_count = db_handle.get_new_matches(request.data['seconds'])
		if match_count == -1:
			return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		return Response({"count":match_count},status=status.HTTP_200_OK)
	else:
		# CRITICAL
		print(f"CRITICAL \"{request.user.id}:{request.user.username}\" is trying to access new_matches API")
	return Response(status=status.HTTP_404_NOT_FOUND)

@permission_classes([IsAuthenticated])
class Logout(APIView):
	# caveat:While sending the GET req,include your token in Header as 
	# "Authorization : Token dahjad3fhhblah blah.."
	# Only using that token, user is identified and token is deleted from table.Hence during login,new token has to be generated.
	@exception_handler
	def post(self, request, format=None):
		name=request.user.username
		try:
			request.user.auth_token.delete()
		except Exception as e:
			# Since req doesn't have token,we can't del it
			print("Error in Logout post ",e)
			return Response(status=status.HTTP_400_BAD_REQUEST)
		else:
			print("Logout of ",name)
			# Return OK
			return Response(status=status.HTTP_200_OK)