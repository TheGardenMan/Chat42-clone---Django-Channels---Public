-- see tables_for_prod.sql
--database
	create database chat;
--profile
	-- user_id is pkey to avoid duplicates
	truncate table profiles cascade;
	create table profiles(user_id integer primary key,username varchar(15),date_of_birth date,gender char,age int,check(age >=13),check(gender in ('m','f')));

	-- create_profile
		-- day in dob is always 1
		-- calc age by urself, and insert
	insert into profiles(user_id,username,date_of_birth,gender,age) values(1,'jaga','1997-09-01','m','23');

	-- get_profile
	select username,age,gender from profiles where user_id=1;
	-- ToDo;write  a sql function to update age for all users.updated once a month.
		-- Age calculator
		select date_part('year',age(date_of_birth)) from profiles where user_id=1;

--preferences
	drop table preferences;
	drop table profiles;
	create table preferences(user_id integer primary key,bio varchar(140),gender_preference char,check(gender_preference in ('m','f','a')),CONSTRAINT create_profile_before_setting_preferences FOREIGN KEY(user_id)REFERENCES profiles(user_id)
		);
	-- set_preferences first time
	insert into preferences(user_id,bio,gender_preference) values(1,'Hello world','m');
	-- set_preferences subsequent
	update preferences set bio='hello Mars',gender_preference='a' where user_id=1;
	-- get_preferences (its two queries:one gets profile details,another gets preferences.We return both of them as one)
	--#1
		select bio,gender_preference from preferences where user_id=1;
	--#2 is in profiles table

--reports
	--  report 
	create table reports(report_id serial,reporter_id integer,reportee_id integer,report_time timestamptz,report_reason integer,report_others_reason varchar(200),resolved boolean);
-- see APIS.txt for report_id values
	insert into reports(reporter_id,reportee_id,report_time,report_reason,report_others_reason,resolved) values (1,2,current_timestamp,1,NULL,0);
	-- report resolved
	update reports set resolved=1 where report_id=1;

--blacklist
	create table blacklist(user_id integer  primary key,reason integer,comment text);
	-- 
	insert into blacklist(user_id,reason,comment) values (1,2,'beep beep')
	--
	def isBlacklisted(user_id):
	    cur.execute("SELECT user_id FROM blacklist WHERE user_id = %s", (user_id,))
	    return cur.fetchone() is not None
-- feedback
	create table feedback(user_id integer, feedback_text varchar(500),feedback_time timestamptz);
	insert into feedback(user_id,feedback_text,feedback_time) values (1,'hello world',current_timestamp);
-- error
	create table errors(error_id SERIAL PRIMARY KEY,user_id integer, error_name text, error_message text, error_flow text, error_time timestamptz );
	insert into errors(user_id,error_name,error_message,error_flow,error_time) values(0,'hello','eee','c:==>kjsfqq',current_timestamp);
-- matches table
	create table matches(match_id SERIAL PRIMARY KEY,user_id1 integer,user_id2 integer, match_time timestamptz);
	insert into matches(user_id1,user_id2,match_time) values(1,2,current_timestamp);
	SELECT count(user_id1) from matches WHERE "match_time" >= NOW() - INTERVAL '500 seconds';