import time
import copy
import json
from . import redis_handle
from . import db_handle
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from rest_framework.authtoken.models import Token
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

def get_user(token_key):
	try:
		token = Token.objects.get(key=token_key)
		return token.user
	except Exception as e:
		print("Error at get_user ", e)
		return None

def handle_ready(self,text_data_as_dict):
	if redis_handle.get_group_name(self.user.id):
		print(f"{self.user.id} already has a group_name.should EXIT before READY.can't READY\n")
		return -1
	# no need to call set_channel_name_in_hset coz channel name is already there since we're already connected
	redis_handle.set_profile_info_in_hset(self.user.id)
	redis_handle.add_user_to_bucket(self.user.id)
	print(f"READY {self.user.id} done")
	return 1

def exception_handler(func):
	# https://stackoverflow.com/a/64212552
	def inner_function(*args, **kwargs):
		# args is a tuple which contains the args passed to target function
		try:
			return func(*args, **kwargs)
		except Exception as e:
			print("\n@exception_handler: started\n")
			# if this function had a user,clean him
			if hasattr(args[0],'user'):
				user_id = args[0].user.id
				#specific to consumer.py
				cleanup_the_user(args[0].user.id)
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
			print(f"{user_id} {error_name} \n{error_message} \n{error_flow}")
			db_handle.error_logger(user_id, error_name, error_message, error_flow)
			print("exception handling done...")
	return inner_function

def send_message_to_group(self, text_data_as_dict):
	# print(text_data_as_dict)
	text_data_as_dict["sender_id"] = self.user.id
	text_data_as_dict["type"] = "handle_each_msg"
	group_name = redis_handle.get_group_name(self.user.id)
	# only self.send() needs str parameters.. everything else needs dict
	if group_name:
		# only self.send() needs str parameters.. everything else (group_send) needs dict
		async_to_sync(self.channel_layer.group_send)(
			group_name, text_data_as_dict)
		print(f"message has been sent to group {group_name} \n")
	else:
		# group_name None
		print(f"group name of {self.user} is {group_name}.So not sending the message\n")

def notify_opponent_left(user_id,opponent_id,opponent_channel_name):
	'''notify OPPONENT_LEFT if opponent exists'''
	if opponent_id:
		print(f"Since {user_id} has an opponent ,we need to notify the  opponent {opponent_id} ")
		# Since {self.user.id} has an opponent ,we need to notify the  opponent {opponent_id}
		async_to_sync(channel_layer.send)(opponent_channel_name, {
			"type": "receive_from_server_side",
			"CMD": "OPPONENT_LEFT",
		})
	else:
		print(f"{user_id} doesn't have an opponent")

def handle_feedback(user_id,text_data_as_dict):
	print(f"FEEDBACK of {user_id}")
	db_handle.add_feedback(user_id,text_data_as_dict["data"])

def handle_exit(user_id):
	'''called when user wants to exit match mode or chat'''
	print(f"EXIT {user_id}")
	opponent_id, opponent_channel_name = redis_handle.exit_the_user(
				user_id)
	notify_opponent_left(user_id, opponent_id, opponent_channel_name)
	print(f"EXIT {user_id} done")

def handle_each_msg_clone(self,text_data_as_dict):
	'''handle_each_msg calls this.. Here for brevity'''
	# message sent directly from client will not have sender_id.Only the messages from group have sender_id
	# text_data is passed as reference.It caused problems.soo
	text_data_as_dict = copy.deepcopy(text_data_as_dict)
	if "sender_id" in text_data_as_dict:
		# the below message is duplicate
		# print(text_data_as_dict["sender_id"]," ",self.user.id," ",text_data_as_dict["sender_id"] == self.user.id," ..")
		if text_data_as_dict["sender_id"] == self.user.id:
			print("@handle_each_msg: sender & receiver are same.Skipping\n")
			return
		else:
			# This message has been received from group to this user(since it has a sender_id) and it's not a duplicate(since we check in above if statement).So let's self.send and return.If we don't return,it will be received by below lines which will keep sending the message to group
			# send message to actual client and return
			# clean up unwanted details.type is  needed.always.
			# since we have "deepcopied",deleting this will not affect other copies that are sent to each user in a group(only one in our case+)
			del text_data_as_dict["sender_id"]
			# Hide the type
			text_data_as_dict["type"] = "client"
			# DND always return json.... Not dict. https://stackoverflow.com/a/63435048/9217577
			self.send(json.dumps(text_data_as_dict))
			print("Sent the message to actual client")
			return
	else:
		print("Warn: @handle_each_msg: there's no sender_id attached to the message.not supposed to happen")

def authenticate(self):
	token = self.scope["query_string"] #b'token=5bef8a8b6f1ed2897a3cfb9085573324c24e8d66'
	if not token:
		print("Nothing was passed in query params")
		return None
	token = token.decode("utf-8")
	token = token.split("=")[1]
	user = get_user(token)
	if not user:
		# gotta be invalid token or malformed data
		print("get_user() failed.rejected")
		return None
	else:
		return user

def load_profile_and_accept(self):
	if redis_handle.set_online(self.user.id, self.channel_name) == 1:
		self.accept()
		print(f"{self.user} connected successfully")
		message=json.dumps({"CMD": "WAIT_FOR_OPPONENT"})
		self.send(message)
		redis_handle.add_to_online_set(self.user.id)
		print("sent WAIT_FOR_OPPONENT \n")
		return
	else:
		# -1 if no profil & None if error
		print("see above error.No profile for this user \n")
		self.close()

def handle_connect(self):
	user = authenticate(self)
	if not user:
		self.close()
		return
	
	print("New authenticated connection ", user)
	self.user = user

	if redis_handle.is_online(self.user.id):
		print(f"Already connected {self.user} {self.user.id} :rejecting\n")
		self.close()
		return
	else:
		# try to load profile & respond ||| reject
		load_profile_and_accept(self)

def cleanup_the_user(user_id):
	print(f"@cleanup_the_user: starting clean up of {user_id}")
	# if user_id has an opponent (say X),X's group_name and opponent_id will be deleted and  id of the X and channel_name will be returned so that we can notify X. 
	opponent_id, opponent_channel_name = redis_handle.exit_the_user(user_id)
	notify_opponent_left(user_id, opponent_id, opponent_channel_name)
	# delete the user profile from hash set
	redis_handle.delete_user_hash_set(user_id)
	print(f"clean up of {user_id} done.")

def handle_real_disconnect(self,close_code):
	#profile of opponent is kept while his group name ad "his" opponent_id is deleted. Means if opponent of this receives "OPPONENT_LEFT", he can simply call "READY" to find another match.
	print(f"\nInitiating real disconnect of {self.user.id} ")
	cleanup_the_user(self.user.id)
	redis_handle.remove_from_online_set(self.user.id)
	print(f"Disconnect complete.real disconnect; user_id: {self.user.id} close_code {close_code}")

def handle_report(user_id, text_data_as_dict):
	#text_data_as_dict.get("report_text") will return None if report_text doesn't exist
	print(f"REPORT from {user_id}")
	report_id = text_data_as_dict["report_id"]
	report_text = text_data_as_dict.get("report_text")
	#check if report_text is invalid
	if report_id == "3" and (not report_text or report_text == ""):
		print(f"ERR: user {user_id} has report_id {report_id} but report_text is \"{report_text}\". Not supposed to happen")
		return
	opponent_id = redis_handle.get_opponent_id(user_id)
	
	if opponent_id:
		db_handle.add_report(user_id, opponent_id, report_id, report_text)
		print(f"REPORT done.Calling EXIT of {user_id}")
		#reported.. Now notify the OPPONENT and end the chat
		handle_exit(user_id)
		return
	else:
		print(f"ERR: user {user_id} is reporting but no opponent found. Weird")

class ChatConsumer(WebsocketConsumer):
	# Note:We deal with groups for sending messages. # We deal with channels for sending commands
	@exception_handler
	def connect(self):
		# todo:chrome doesn't allow passing token in headers. so pass it as query_params via WS and handle in server accordingly.
		handle_connect(self)
		
	def handle_each_msg(self,text_data_as_dict):
		handle_each_msg_clone(self,text_data_as_dict)

	@exception_handler
	def receive(self, text_data):
		# here data is str.we make it  dict by json
		if isinstance(text_data, str):  # if coming from client,it will be str.else it will be dict
			text_data_as_dict = json.loads(text_data)

		if text_data_as_dict["CMD"] == "MSG":
			send_message_to_group(self,text_data_as_dict)
			return
		elif text_data_as_dict["CMD"] == "READY":
			if handle_ready(self,text_data_as_dict) == -1:
				# if calling READY when not EXITed (not EXITed means user still has a group_name),reply ERROR
				#when user wants to go to next user, they can call EXIT & READY
				async_to_sync(channel_layer.send)(self.channel_name, {
						"type": "receive_from_server_side",
						"CMD": "ERROR",
				})
			return
		elif text_data_as_dict["CMD"] == "EXIT":
			handle_exit(self.user.id)
			return
		elif text_data_as_dict["CMD"] == "FEEDBACK":
			handle_feedback(self.user.id,text_data_as_dict)
			return
		elif text_data_as_dict["CMD"] == "REPORT":
			#handle_report calls the handle_exit to notify the opponent
			handle_report(self.user.id,text_data_as_dict)
			return
		print(f"@receive: {text_data_as_dict} {self.user.id} {self.user} ")

	# Question: What to do if client emulates server-side-channel layers behaviour.
	# Answer:Process client calls in one function(i.e receive).That function should accept only client messages (REPORT) and reject server messages(MATCH_FOUND).Process system calls in another function(i.e below func receive_from_server_side).Since client can only call receive,system calls can't be made by client.
	@exception_handler
	def receive_from_server_side(self, message):
		# type of incoming data is dict since this is called only from server
		# {'type': 'receive_from_server_side', 'CMD': 'OPPONENT_DETAILS', 'data': {'username': 'qwert', 'age': '34', 'gender': 'f', 'bio': 'Hi there!'}}
		print("@receive_from_server_side \n ", message)
		# warn:IDK why.but "type" is needed.Below "client" type is not used.But needed.So let's hide the name "receive_from_server_side" below
		message["type"] = "client"
		cmd = message["CMD"]
		if cmd == "OPPONENT_DETAILS":
			self.send(json.dumps(message))
			print(f"Sending {cmd} to client\n")
		# this gets called from disconnect()
		elif cmd == "OPPONENT_LEFT":
			print(f"Sending {cmd} to {self.user.id}")
			# send directly client OPPONENT_LEFT
			self.send(json.dumps(message))
			print(f"{cmd} sent to {self.user.id} \n")
		elif cmd == "ERROR":
			print(f"Sending {cmd} to {self.user.id}")
			# send directly client ERROR
			self.send(json.dumps(message))
			print(f"{cmd} sent to {self.user.id} \n")
		else:
			print("..place_holder...")

	@exception_handler
	def disconnect(self, close_code):
		# detection of disconnection of duplicate connection. # If self.channel_name exists in Redis ,exit+the-user and delete hash set.Coz real connection.else do nothing.Coz duplicate connection. # improvement:we should do this in redis_handle once we async all python.This will reduce load on consumer 
		# dont use "if not self.user"
		if not hasattr(self, 'user'):
			# unauthenticated connection. user.id doesn't exist
			print("warn: unauthenticated connection force disconnect")
			return

		# each connection has unique channel.We store channel of each connection.When stored channel and "current" channel are different,we conclude that this disconnect was caused by "duplicate connection" (Means user_id already existed in Redis with a diff channel_name)
		if redis_handle.get_channel(self.user.id) == self.channel_name:
			handle_real_disconnect(self,close_code)
		else:
			print(f"duplicate connection disconnect {self.user.id}, close_code {close_code}\n")