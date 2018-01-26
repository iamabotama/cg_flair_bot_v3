import praw
from collections import deque
import re
import yaml
import os
import config
import math
import time

#Set globals

r=praw.Reddit(user_agent=config.app_user_agent,
              username=config.app_user_name,
              password= config.app_password,
              client_id= config.app_id,
              client_secret= config.app_secret
              )
sub = r.subreddit(config.app_site_name)


class Bot():

    def __init__(self):


        
        
        #store up to 500 link/author pairs
        self.link_authors = deque([],maxlen=500)

        #get cache of authors and links awarded
        self.author_points = yaml.load(sub.wiki['flairbot'].content_md)
        
        """ SET TO Total number of posts for a full refresh.  Be sure to wipe out all flair and wiki page content first """
        self.MAX_POSTS_CHECKED = 150
        
        #track total posts (max = 100 using streams.)
        self.TOTAL_CREATION_GIF_POSTS = 0
        
    def run(self):
        self.scan_submissions()

    def get_OP(self, link_id):

        #first check cache for if we already have this name
        for entry in self.link_authors:
            if entry[0]==link_id:
                return entry[1]
                break

        #then fetch and add it
        else:
            link = next(r.info([link_id]))
            author = link.author
            if author is None:
                self.link_authors.append((link_id,None))
                return None
            else:
                self.link_authors.append((link_id,author.name))
                return author.name

    def score_class(self, score):

        # write out Flair Class
        flair_class = "score-"
        
        for item in score:
            if item >= 1:
                flair_class += "1"
            else:
                flair_class += "0"
        return flair_class

    def score_text(self,score):
        
        #Create a String for each Score_position
        karma_max = ""
        total_posts = "" 
        gold_given = ""

        if (score[0] >= 1000) and (score[0] < 10000):
            total_posts = str(math.floor(score[0]/1000)) + "k"
        if (score[0] >= 100) and (score[0] < 1000):
            total_posts = str(math.floor(score[0]/100)) + "h"
        if (score[0] >= 10) and (score[0] < 100):
            total_posts = str(score[0])    
        if (score[0] > 0) and (score[0] < 10):
            total_posts = "0" + str(score[0])

        if (score[1] >= 100 and score[1] <1000):
            karma_max = str(math.floor(score[1]/100)) + "h"
        if (score[1] >= 1000):
            karma_max = str(math.floor(score[1]/1000)) + "k"
            
        if (score[2] > 0) and (score[2] <10):
            gold_given = "0" + str(score[2])
        if (score[2] > 10) and (score[2] <100):
            gold_given = str(score[2])

        if len(total_posts) >= 1:
            total_posts += " "

        if len(karma_max) >= 1:
            karma_max += " "
        
        flair_text = total_posts + karma_max + gold_given
            
        return flair_text 


    def scan_submissions(self):
        #Awesome!  It's working! :)

        # -> subreddit = r.subreddit(config.app_site_name)
        # -> use this code, to traverse the entire sub: -> for submission in r.subreddit(config.app_site_name).submissions(0, 0):
        for submission in r.subreddit(config.app_site_name).stream.submissions(): 
            #reset Score values
            score = [0,0,0]
            if submission.author_flair_css_class == "reset":
                if submission.author.name in self.author_points:
                    #returns the number of list items under teh authors name.
                    score[0] = len(self.author_points[submission.subreddit.display_name][submission.author.name])
                
                    
                flair_class = self.score_class(score)
                flair_text = self.score_text(score)

                
                submission.subreddit.flair.set(submission.author, text=flair_text, css_class = flair_class)
                print('reset flair for /u/'+submission.author.name+' in /r/'+submission.subreddit.display_name)
                continue
            
            if submission.author.name == "botsbot":
                print("botsbot debug point")
            #only manage flair for Creation Gifs
            if submission.subreddit.display_name != config.app_site_name:
                continue

            self.TOTAL_CREATION_GIF_POSTS += 1
            #kick out after checking X posts. (MAX_POSTS_CHECKED is set in class initialization)
            if self.TOTAL_CREATION_GIF_POSTS >= self.MAX_POSTS_CHECKED :
                return
            
            print(submission.author.name + ": entry#:" + str(self.TOTAL_CREATION_GIF_POSTS))
            #make sure user exists
            if submission.author is None:
                continue

            # Check to see if further processing is required            
            additional_processing_required = False

            #ignore posts with less than 10 Karma
            if submission.score < 10 :
                continue

            #add user to authorpoints
            if submission.subreddit.display_name not in self.author_points:
                self.author_points[submission.subreddit.display_name]={}
                additional_processing_required = True
            if submission.author.name not in self.author_points[submission.subreddit.display_name]:
                self.author_points[submission.subreddit.display_name][submission.author.name]={}
                additional_processing_required = True
            if submission.id not in self.author_points[submission.subreddit.display_name][submission.author.name]:
                self.author_points[submission.subreddit.display_name][submission.author.name][submission.id] = [submission.score, submission.gilded]
                additional_processing_required = True
           
            
            #check sumbimission for gold
            if submission.gilded > 0:
                additional_processing_required = True

            if submission.score >= 100:
                additional_processing_required = True
               
            #check to see if user has scored this thread
            #if submission.id in self.author_points[submission.subreddit.display_name][submission.author.name] and additional_processing_required == False:
            if additional_processing_required == False:
                continue
            
            #add user to authorpoints
            #self.author_points[submission.subreddit.display_name][submission.author.name].append(submission.id)

            #get new score and flair text
            # Take the length (total number) of Submissions in Wiki after this one has been added and place it in pos 0 of score list
            score[0] = len(self.author_points[submission.subreddit.display_name][submission.author.name])
            
            is_gilded = self.author_points[submission.subreddit.display_name][submission.author.name][submission.id][1]
            karma_size = self.author_points[submission.subreddit.display_name][submission.author.name][submission.id][0]

            for sub_id in self.author_points[submission.subreddit.display_name][submission.author.name]:
                if karma_size >= 100 or self.author_points[submission.subreddit.display_name][submission.author.name][sub_id][0] >= 100:
                    score[1] = max(score[1],max(karma_size,self.author_points[submission.subreddit.display_name][submission.author.name][sub_id][0]))
                    
                # count up existing gold
                score[2] += self.author_points[submission.subreddit.display_name][submission.author.name][sub_id][1]
            #add new gold to existing gold
            score[2] += (submission.gilded - is_gilded)
            
            flair_class = self.score_class(score)
            flair_text = self.score_text(score)

            #update score flair text and class
            submission.subreddit.flair.set(redditor=submission.author, text=flair_text, css_class=flair_class)


            #save new authorpoints to wiki

            reason = "/u/"+submission.author.name+" has "+flair_text+" in /r/"+submission.subreddit.display_name+" at "+submission.id
            sub.wiki['flairbot'].edit(yaml.dump(self.author_points, explicit_start=True, indent=4).replace('\n','\n    '),reason=reason)
            print(submission.author.name+" scored in /r/"+submission.subreddit.display_name)

            print(submission.author.name)
            print(flair_class)
            print(flair_text)


if __name__=="__main__":
    while True:
        bot=Bot()
        bot.run()
        print("Cycle complete, sleeping for 60 seconds")
        time.sleep(60)
        #sleeping for 10 seconds
	    