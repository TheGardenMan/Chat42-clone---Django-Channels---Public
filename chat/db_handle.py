from datetime import datetime, date
import psycopg2
import re
import os
# cant access settings here since it is relative but this module is accessed by algo.py
user = os.environ['postgres_username']
password = os.environ['postgres_password']
port = os.environ['postgres_port']

try:
	connection = psycopg2.connect(user = user,
								  password = password,
								  host = "127.0.0.1",
								  port = port,
								  database = "chat")
	cursor = connection.cursor()

except (Exception, psycopg2.Error) as error :
	print ("Error while connecting to PostgreSQL", error)
	isError=True

#username_check
def username_check(username):
	cursor.execute("select count(username) from auth_user where username=%s",(username,))
	count=cursor.fetchone()
	count=f"{count[0]}"
	# Assuming there's maximum one username
	if count=="0":
		return 1 #Available
	return -1 #Not available

# used by redis_handle & views
def get_profile_and_preferences(user_id):
	try:
		cursor.execute("select bio,gender_preference from preferences where user_id=%(user_id)s",{'user_id':user_id})
		result_1=cursor.fetchone()
		bio,gender_preference=result_1[0],result_1[1]

		cursor.execute("select username,age,gender from profiles where user_id=%(user_id)s",{'user_id':user_id})
		result_2=cursor.fetchone()
		username,age,gender=result_2[0],result_2[1],result_2[2]
		profile_info = {"username": username, "gender": gender, "age": age, "bio": bio,"gender_preference": gender_preference}
		return profile_info
	except Exception as e:
		print("Error in get_profile_and_preferences ",e)
		# improvement
		return -1

def calculate_age(month,year):
	# we assume the date to be 01
	temp_dob=''.join(['01',month,year])
	date_of_birth = datetime.strptime(temp_dob, "%d%m%Y")
	today = date.today()
	return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

def get_username(user_id):
	#Not very safe but does the job. To prevent SQL injection: https://realpython.com/prevent-python-sql-injection/#crafting-safe-query-parameters
	cursor.execute("select username from auth_user where id=%(user_id)s",{'user_id': user_id})
	username=cursor.fetchone()
	return f"{username[0]}"

def set_initial_preferences(user_id):
	cursor.execute("insert into preferences(user_id,bio,gender_preference) values(%(user_id)s,'Hi there!','a');",{'user_id': user_id})
	connection.commit()

def create_profile(user_id,gender,birth_month,birth_year):
	# if not rolled back properly during error inside DB,InSQLFailedTransaction will occur
	age=calculate_age(birth_month,birth_year)
	username=get_username(user_id)
	# 'YYYY-MM-DD'.
	date_of_birth=''.join([birth_year,"-",birth_month,"-","01"])
	# age and gender are checked by constraints in db
	try:
		cursor.execute("insert into profiles(user_id,username,date_of_birth,gender,age) values(%(user_id)s,%(username)s,%(date_of_birth)s,%(gender)s,%(age)s);",{'user_id':user_id,'username':username,'date_of_birth':date_of_birth,'gender':gender,'age':age})
		# set default prefs
		set_initial_preferences(user_id)
	except Exception as e:
		connection.rollback()
		print(f"error in create_profile of {user_id} {e} ")
		return -1
	else:
		connection.commit()
		return 1

def set_preferences(user_id,gender_preference,bio):
	# preferences table references profiles table.so we will get error if someone calls set_preferences before create_profile.if error occurs,we will redirect user to create_profile page
	try:
		cursor.execute("update preferences set bio=%(bio)s,gender_preference=%(gender_preference)s where user_id=%(user_id)s;",{'bio':bio,'gender_preference':gender_preference,'user_id':user_id})
	except Exception as e:
		print("error in set_preferences ",e)
		connection.rollback()
		return -1
	else:
		connection.commit()
		return 1

def add_feedback(user_id,feedback_text):
	try:
		cursor.execute("insert into feedback(user_id,feedback_text,feedback_time) values (%(user_id)s,%(feedback_text)s,current_timestamp);",{'user_id':user_id,'feedback_text':feedback_text});
	except Exception as e:
		print("Error @ add_feedback: ",e)
		connection.rollback()
		return -1
	else:
		connection.commit()
		return 1

def error_logger(user_id, error_name, error_message, error_flow):
	try:
		cursor.execute("insert into errors(user_id,error_name,error_message,error_flow,error_time) values(%(user_id)s,%(error_name)s,%(error_message)s,%(error_flow)s,current_timestamp);",{'user_id':user_id, 'error_name':error_name, 'error_message':error_message, 'error_flow':error_flow})
	except Exception as e:
		print("Error @ error_logger: ",e)
		connection.rollback()
	else:
		connection.commit()

def add_report(reporter_id,reportee_id,report_reason,report_others_reason=None):
	#sanitize user data to prevent SQL injections.. only alphanumeric is allowed
	if report_others_reason:
		report_others_reason = re.sub(r"[^a-zA-Z0-9 ]", "", report_others_reason)
		print(f"@add_report {reporter_id} {reportee_id} {report_reason} {report_others_reason}")
	else:
		print(f"@add_report {reporter_id} {reportee_id} {report_reason} .. No report_text")
	try:
		cursor.execute("insert into reports(reporter_id,reportee_id,report_time,report_reason,report_others_reason,resolved) values (%(reporter_id)s,%(reportee_id)s,current_timestamp,%(report_reason)s,%(report_others_reason)s,'f');",{'reporter_id':reporter_id, 'reportee_id':reportee_id, 'report_reason':report_reason, 'report_others_reason':report_others_reason})
	except Exception as e:
		print("Error @ add_report: This won't be logged since it has been caught ",e)
		connection.rollback()
	else:
		connection.commit()

def add_match(user_id1, user_id2):
	try:
		cursor.execute("insert into matches(user_id1,user_id2,match_time) values(%(user_id1)s,%(user_id2)s,current_timestamp);",{'user_id1': user_id1,'user_id2': user_id2})
	except Exception as e:
		print("Error @ db_handle.add_match",user_id1,user_id2,e)
		connection.rollback()
	else:
		print(f"@db_handle.add_match {user_id1} {user_id2} done")
		connection.commit()

def get_new_matches(seconds):
	seconds = int(seconds)
	try:
		cursor.execute("SELECT count(user_id1) from matches WHERE \"match_time\" >= NOW() - INTERVAL '%(seconds)s seconds';",{'seconds':seconds})
		# (count,)
		return cursor.fetchone()[0]
	except Exception as e:
		print("Error @ get_new_matches")
		return -1
