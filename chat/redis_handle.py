from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
channel_layer = get_channel_layer()
from . import db_handle
import redis

# change redis url here..
redis_client = redis.Redis(host='localhost', port=6379, db=0)
print("****warning :using flushdb for logging out users in redis_handle.py .disable me in prod*** \n")
redis_client.flushdb()

sets=["mm","ma","mf","ff","fa","fm"]
def return_handle():
	return redis_client

# Used to calculate no of users online
def add_to_online_set(user_id):
	redis_client.sadd("online", user_id)

def remove_from_online_set(user_id):
	redis_client.srem("online", user_id)

def get_online_users_count():
	return redis_client.scard("online")

def is_online(user_id):
	# check whether the key exists.This key has a "hash-set" as value
	if redis_client.exists(user_id) == 1:
		# already connected
		return True
		# not connected
	return False

def set_channel_name_in_hset(user_id, channel_name):
	'''load channel_name into redis'''
	redis_client.hset(user_id, mapping={"channel_name": channel_name})

def set_profile_info_in_hset(user_id):
	'''load profile info from db into Redis'''
	print(f"@set_profile_info_in_hset setting profile of {user_id}")
	profile_info = db_handle.get_profile_and_preferences(user_id)
	if profile_info==-1:
		print("No profile for user ", user_id)
		return -1
	redis_client.hset(user_id, mapping=profile_info)
	print("profile has been set")
	return 1


def add_user_to_bucket(user_id):
	bucket_name = get_bucket_name(user_id)
	print(f"@add_user_to_bucket: Adding {user_id} to bucket {bucket_name}")
	redis_client.sadd(bucket_name, user_id)

def create_or_update_user_hset(user_id, channel_name):
	set_channel_name_in_hset(user_id, channel_name)
	return set_profile_info_in_hset(user_id)

def set_online(user_id, channel_name):
	if create_or_update_user_hset(user_id, channel_name) == 1:
		add_user_to_bucket(user_id)
		return 1
	else:
		# Error at create_or_update_user_hset
		return -1

def get_profile(user_id):
	profile_details = redis_client.hgetall(user_id)
	result = {}
	for key in profile_details:
		# get the data from key n decode
		data = profile_details[key].decode('utf-8')
		# decode the  key
		key = key.decode('utf-8')
		# store decoded data in decoded key
		result[key] = data
	return result


def get_channel(user_id):
	channel_name = redis_client.hget(user_id, "channel_name")
	# You can't decode "None"
	if not channel_name:
		print(
			f"Warning: user_id :{user_id} doesn't have a channel_name.Redis might not have been flushed well")
		return None
	return channel_name.decode('utf-8')

def get_group_name(user_id):
	group_name = redis_client.hget(user_id, "group_name")
	# You can't decode "None"
	if not group_name:
		print(f"user_id :{user_id} doesn't have a group_name")
		return None
	return group_name.decode('utf-8')

def get_bucket_name(user_id):
	raw_bucket_name = redis_client.hmget(user_id, "gender", "gender_preference")
	# raw_bucket_name is [m,m] ..... or [None,None]
	# mm,mf,fm,ff,fa,ma
	if raw_bucket_name[0]==None:
		print(f"{user_id} doesn't have a bucket_name.Returning None")
		return None
	bucket_name = ''.join([raw_bucket_name[0].decode(
		'utf-8'), raw_bucket_name[1].decode('utf-8')])
	return bucket_name

def delete_user_from_bucket(user_id):
	'''if user and the bucket exists, he will be removed'''
	bucket_name = get_bucket_name(user_id)
	if bucket_name:
		if redis_client.exists(bucket_name):
			redis_client.srem(bucket_name, user_id)

def discard_group(group_name, channel_name):
	print(f"discarding group_name {group_name}")
	async_to_sync(channel_layer.group_discard)(group_name, channel_name)

def flush_group_and_return_opponent(user_id):
	if redis_client.hexists(user_id, "group_name"):
		group_name = get_group_name(user_id)
		print(f"user {user_id} has a group")
				# opponent clearance
		# get the opponent_id
		opponent_id = redis_client.hget(user_id, "opponent_id")
		# remove opponent from group
		discard_group(group_name,get_channel(opponent_id))
		# remove group_name of opponent
		redis_client.hdel(opponent_id, "group_name")
		# remove opponent_id of opponent
		redis_client.hdel(opponent_id, "opponent_id")
		#-------------#
				# user clearance
		# remove user from group
		discard_group(group_name,get_channel(user_id))
		# remove group_name of user
		redis_client.hdel(user_id, "group_name")
		# remove opponent_id of user
		redis_client.hdel(user_id, "opponent_id")
		return opponent_id
	else:
		return None

def free_the_user(user_id):
	'''user profile will be kept but user will be removed from bucket and his group details will be removed'''
	# READY will update the profile to latest (while keeping the channel_name).Deleting profile here and updating (override) it in READY is useless.So simply keeping the profile n override it in READY
	# remove the user_id from set
	delete_user_from_bucket(user_id)
	# flush_group_and_return_opponent
	opponent_id = flush_group_and_return_opponent(user_id)
	return opponent_id

def exit_the_user(user_id):
	print(f"Exiting the user {user_id}")
	opponent_id = free_the_user(user_id)
	if opponent_id:
		# return the opponent_id so that they can be notified OPPONENT_LEFT
		return opponent_id, get_channel(opponent_id)
	else:
		# user_id doesn't have an opponent.So we have no one to notify
		return None, None

def delete_user_hash_set(user_id):
	print(f"Deleting hash set of {user_id}")
	# flush the hash_set of the user_id
	redis_client.delete(user_id)

def get_opponent_id(user_id):
	opponent_id = redis_client.hget(user_id, "opponent_id")
	if opponent_id:
		return opponent_id.decode('utf-8')
	return None

# create a room for every user..Front-end requests for match.Once matched,we send them a chat room URL which both clients connect ..then they chat
# How to send a message to a particular client through websockets:https://stackoverflow.com/a/39668242/9217577
# Uniquely finding a channel and sending them a message:see the second snippet in below link
# https://channels.readthedocs.io/en/latest/topics/channel_layers.html#single-channels
# Client creates a websocket and waits
# Store user_ids and their channel names in db
# Good WebSocket example:https://channels.readthedocs.io/en/latest/topics/channel_layers.html#single-channels
# LW:use sets for tracking online users... one set for all users
# 	sadd -add user_id to set
# 	sismember -online or not
# 	srem -remove user_id list
# 	spop - remove two users from list -use this for selecting 2 random ppl to match.Once match fails,both of them should be added to the "online" set
# 	dont use srandmember.It will cause duplicates while selecting two members
# """