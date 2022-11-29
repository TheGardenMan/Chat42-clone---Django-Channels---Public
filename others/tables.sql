create database chat;
create table profiles(user_id integer primary key,username varchar(15),date_of_birth date,gender char,age int,check(age >=13),check(gender in ('m','f')));
create table preferences(user_id integer primary key,bio varchar(140),gender_preference char,check(gender_preference in ('m','f','a')),CONSTRAINT create_profile_before_setting_preferences FOREIGN KEY(user_id)REFERENCES profiles(user_id));
create table matches(match_id SERIAL PRIMARY KEY,user_id1 integer,user_id2 integer, match_time timestamptz);
create table reports(report_id serial,reporter_id integer,reportee_id integer,report_time timestamptz,report_reason integer,report_others_reason varchar(200),resolved boolean);
create table feedback(user_id integer, feedback_text varchar(500),feedback_time timestamptz);
create table errors(error_id SERIAL PRIMARY KEY,user_id integer, error_name text, error_message text, error_flow text, error_time timestamptz );