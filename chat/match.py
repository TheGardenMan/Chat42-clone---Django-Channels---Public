import os
import redis
# Don't do from . import db_handle.Since this imports db_handle, we need to store postgres credentials in this service's file also
import db_handle
# do not import redis_handle.It will import db_handle like "from . import db_handle" and cause import error.Because we run this file separately

#django settings is required by channels (it gets channel_layers from it).Since we run channels outside Django,we set them here .Shd be set b4 importing channels.Ref:https://pytest-django.readthedocs.io/en/latest/configuring_django.html#using-django-conf-settings-configure
from django.conf import settings
settings.configure(
	CHANNEL_LAYERS = {
		'default': {
			'BACKEND': 'channels_redis.core.RedisChannelLayer',
			'CONFIG': {
				"hosts": [('127.0.0.1', 6379)],
			},
		},
	}
	)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()

redis_client = redis.Redis(host='localhost', port=6379, db=0)
sets=["mm","ma","mf","ff","fa","fm"]

def get_channel_(user_id):
	channel_name=redis_client.hget(user_id,"channel_name")
	# You can't decode "None"
	if not channel_name:
		print("Warning: user_id :",user_id," doesn't have a channel_name")
		return None
	return channel_name.decode('utf-8')

def get_profile(user_id):
	profile_details=redis_client.hmget(user_id,["username", "age","gender","bio"])
	result={"username":profile_details[0].decode('utf-8'),"age":profile_details[1].decode('utf-8'),"gender":profile_details[2].decode('utf-8'),"bio":profile_details[3].decode('utf-8')}
	return result

def load_test_data_to_redis():
	for i in range(1,100):
		redis_client.sadd(sets[i%6],i)

def pop_one_user_from_given_sets(list_of_sets):
	for i,set_name_ in enumerate(list_of_sets):
		temp_user2=redis_client.spop(set_name_)
		if temp_user2!=None:
			# decoding at match_finder
			return temp_user2
	return None

# print(pop_one_user_from_given_sets(["mm","ma"]))
# if shouldFilterStrictly is True in Env var,here also true.if not set or some other value is set, then False
shouldFilterStrictly=(os.getenv('should_filter_strictly', 'False') == 'True')
if shouldFilterStrictly:
	# try given filters only
	# priority is to have maximum m,f pairs possible
	print("respecting filters")
	mm_match_set=["mm","ma"]
	ma_match_set=["fm","fa","ma","mm"]
	mf_match_set=["fm","fa"]
	ff_match_set=["ff","fa"]
	fa_match_set=["mf","ma","fa","ff"]
	fm_match_set=["mf","ma"]
else:
	# try filters first.If not found,try other sets too
	print("Be warnedddddddddddddddddddddddddddddddddddddddd.not respecting filters")
	# ordered in such a way to maximize (m,f) pairs
	mm_match_set=["mm","ma","mf","ff","fa","fm"]
	ma_match_set=["fm","fa","ma","mm","ff","mf"]
	mf_match_set=["fm","fa","ff","mm","ma","mf"]
	ff_match_set=["ff","fa","mm","ma","mf","fm"]
	fa_match_set=["mf","ma","fa","ff","mm","fm"]
	fm_match_set=["mf","ma","mm","fa","ff","fm"]

def match_finder(source_set_name):
	# DND --> ToDo --> we keep popping a user and putting im back.Too many inserts.So use "srandmember" safely (means without getting duplicates.. we will get duplicates only if two users are in same sets) and pop the user1 only if a match was found.else do nothing.srandmember doesn't remove the user1 so we don't have yo put him back
	# pop a user user1
	user1=redis_client.spop(source_set_name)
	# no users in bucket.So return None
	if user1==None:
		return None,None
	# find a match for user1
	# keeping it naive for readability
	if source_set_name=="mm": #mm
		user2=pop_one_user_from_given_sets(mm_match_set)
	elif source_set_name=="ma":
		user2=pop_one_user_from_given_sets(ma_match_set)
	elif source_set_name=="mf":
		user2=pop_one_user_from_given_sets(mf_match_set)
	elif source_set_name=="ff":
		user2=pop_one_user_from_given_sets(ff_match_set)
	elif source_set_name=="fa":
		user2=pop_one_user_from_given_sets(fa_match_set)
	elif source_set_name=="fm":
		user2=pop_one_user_from_given_sets(fm_match_set)
	if user1:
		user1=user1.decode('utf-8')
	if user2:
		user2=user2.decode('utf-8')
	# match not found for user1.so put user1 back into his set
	if user2 == None:
		redis_client.sadd(source_set_name,user1)
	return user1,user2

def create_group_for_given_users(user1,user2):
	# At least one of the receievd users will always be not None
	print("Group received ",user1,user2)
	if user1:
		user1_channel=get_channel_(user1)
	if user2:
		user2_channel=get_channel_(user2)
	# no need to check if user2 is None in the below line.Coz one of them is always not None
	if user1==None:
		#do not notify user1 OPPONENT_NOT_FOUND.Timeout in client instead
		#async_to_sync(channel_layer.send)(user2_channel, {
		#	"type": "receive_from_server_side",
		#	"CMD": "OPPONENT_NOT_FOUND",
		#})
		return

	if user2==None:
		#do not notify user1 OPPONENT_NOT_FOUND.Timeout in client instead
		#async_to_sync(channel_layer.send)(user1_channel, {
		#	"type": "receive_from_server_side",
		#	"CMD": "OPPONENT_NOT_FOUND",
		#})
		return

	# lets make it as "user1<user2" always.Dont do this above.Coz here all of them are not_None.But above ,one of them might be not None and you cant compare None to a number
	if int(user1)>int(user2):
		user1,user2=user2,user1
		# swap the channels too
		user1_channel,user2_channel=user2_channel,user1_channel
	print(user1,user2)
	# create group & add channels
	group_name=''.join(["g_",user1,"_",user2])
	async_to_sync(channel_layer.group_add)(group_name,user1_channel)
	async_to_sync(channel_layer.group_add)(group_name,user2_channel)
	# store the group_name & opponent_id to redis
	redis_client.hset(user1,mapping={"group_name":group_name,"opponent_id":user2})
	redis_client.hset(user2,mapping={"group_name":group_name,"opponent_id":user1})
	# test the group
	# async_to_sync(channel_layer.group_send)(group_name, {"type":"receive_from_server_side","CMD":"Group has been created"})
	# send OPPONENT_DETAILS
	async_to_sync(channel_layer.send)(user1_channel, {
		"type": "receive_from_server_side",
		"CMD": "OPPONENT_DETAILS",
		"data":get_profile(user2) 
	})
	async_to_sync(channel_layer.send)(user2_channel, {
		"type": "receive_from_server_side",
		"CMD": "OPPONENT_DETAILS",
		"data":get_profile(user1)
	})
	db_handle.add_match(user1,user2)
# print(match_finder("mm"))


set_id=-1

# use Procfile n run multiple processes
# matchxyz: python chat/match.py #here matchxyz is just a name for the process
# https://stackoverflow.com/a/22991644

def get_online_users_count():
	count = 0
	for set_name in sets:
		set_count =  redis_client.scard(set_name)
		print(set_name,set_count)
		count = count+set_count
	print("Online users count", count)
# ==matters==
# c=0
import time
print("Matcher started")
while True:
	# get_online_users_count()
	set_id+=1
	set_name=sets[set_id]
	user1=None
	user2=None
	# checking whether set is empty by set_length...returns int not str.Timecomplexity O(1)
	if redis_client.scard(set_name)!=0:
		user1,user2=match_finder(set_name)
		# if one of the users is not None,they have to be notified about OPPONENT_NOT_FOUND..So we pass them
		# but if both are None,it's useless to pass
		if user1!=None and user2!=None:
			print(f"Match found: {user1} , {user2}")
			create_group_for_given_users(user1,user2)
	# else:
		# print(set_name," is empty")
		# c+=1
	# bug:remove  below 2 lines
	# if c==6:
	#	break
	#bug above
	if set_id==5:
		set_id=-1
	# Limiting CPU usage.While "sleeping", other processes can execute.
	time.sleep(0.02)
	# break