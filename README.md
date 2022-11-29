# Real time chat website using Django Channels and Redis
Inspired by https://chat42.online

Backend is complete. Front-end is incomplete.

Users are matched based on their gender preferences.

File `chat\match.py` should be run as a separate process and it puts two users into chats if they meet each others gender preference.

API details are in `others\APIs.notes`

ORM is not used. SQL statements to create tables are in `others\tables.sql`

Environment variables are
`django_settings_module=mysite.prod_settings`

`should_filter_strictly=True` (If `True` , only users who match your preference will be matched)


`postgres_username,postgres_password,postgres_port,secret_key,admin_username,admin_user_id`


