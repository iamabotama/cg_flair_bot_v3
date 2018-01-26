import praw 
import config

def bot_login():
	#print("Logging in....")
	r = praw.Reddit(username = config.app_user_name,
			password = config.app_password,
			client_id = config.app_id,
			client_secret = config.app_secret,
			user_agent=config.app_user_agent)
	print("Logged in...")
	return r