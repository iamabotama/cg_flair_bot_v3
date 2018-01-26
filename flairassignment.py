#This script assigns a flair class to all users with an un-classed flair. This is necessary because PlusBot freely overwrites un-flaired and un-classed users.

import praw
import config
import login




#change this for the sub you are preparing
subreddit_name = 'iamabotama'

#r=praw.Reddit('PlusBot flair class assignment')
#r.login(input('username: '),input('password: '))

r = praw.Reddit(username = config.app_user_name,
		password = config.app_password,
		client_id = config.app_id,
		client_secret = config.app_secret,
		user_agent=config.app_user_agent)


subreddit = r.subreddit(subreddit_name)



#get flair list
#flairlist = r.get_flair_list(subreddit, limit=None)
flairlist = []

for flair in subreddit.flair(limit=None):
    print(flair)


#this is important enough that it's worth protecting against a typo
new_class = input('New CSS class (no spaces allowed):')
if " " in new_class:
    raise ValueError("new class cannot contain whitespace")      


new_flairs = []

#iterate through flair list and look for users with un-classed flair
for flair in flairlist:

    new_flair = flair
    
    if not flair['flair_css_class']:
        new_flair['flair_css_class']=new_class
        new_flairs.append(new_flair)

#Set new flairs
if new_flairs:
    r.set_flair_csv(subreddit, new_flairs)

#get flair choices
f=r.get_flair_choices(subreddit)['choices']

#clear existing flair templates
r.clear_flair_templates(subreddit)

#Ensure that userflairs are enabled and displayed and that users can reset their flair to their points
r.add_flair_template(subreddit, text = "Score (comment anywhere)", css_class = "reset")


for flair in f:
    if not flair['flair_css_class']:
        r.add_flair_template(subreddit, text=flair['flair_text'], css_class=new_class)
    else:
        r.add_flair_template(subreddit, text=flair['flair_text'],css_class=flair['flair_css_class'])


