import fourch
import time
import tweepy
from datetime import datetime

#An explaination about the GET class:
# The GET class contains information about a board, it's current post id,
# an older post id for reference, the next GET that will occur on the board,
# and if the GET has been tweeted about yet.
# The get_*() functions (get_time_until(), get_next_GET(), etc.) operate similar to public accesors,
# however they are a bit different.
# These functions also update the member variable corresponding to the function; they are like a get and a set.
# I have tried and partially failed at making this class reusable by other things; I suggest you read it through before using.


class GET:
    def __init__(self, board, alg):
        self.board = board
        self.current_post = 0   #will be a fourch.reply object
        self.last_post = 0      #will also be a fourch.reply object
        if alg == "push":
            self.push_posts()
        elif alg == "total":    #could use better trigger word
            self.update_posts()
        self.next_GET = 0
        self.next_GET = self.get_next_GET()
        
    def push_posts(self):
        """Post managing function 1: set current_post to the latest post on the board, set last_post to the older current_post"""
        #pushes the current_post into the last_post
        self.last_post = self.current_post
        #get current post on the board
        threads = fourch.board(self.board).page(1, update_each=True)
        for thread in threads:
            if (not thread.op.sticky) and thread.replies:
                self.current_post = thread.replies[-1]
                break
               
    def update_posts(self):
        """Post managing function 2: set current_post to the latest post on the board, set last_post to the last post on the board"""
        #get current post on the board
        page = 1
        retry = True
        while retry:
            threads = fourch.board(self.board).page(page, update_each=True)
            for thread in threads:
                if (not thread.op.sticky) and thread.replies:
                    self.current_post = thread.replies[-1]
                    retry = False
                    break
            page += 1   #this will ONLY occur if the entire 1st page is stickied (this has happened on [s4s])
        #get last post on the board
        fboard = fourch.board(self.board) 
        page = fboard.threads()[-1]['page'] #get the lowest page
        retry = True
        while retry:
            try:
                threads = fboard.page(page, update_each=True)
                retry = False
            except Exception as e:
                if '404' in e.message:  #page is 404
                    page -= 1   #select the next page going down
                    retry = True
                else:
                    raise
            except:
                raise
        for thread in reversed(threads):
            if thread.replies:
                self.last_post = thread.replies[-1]
                break
        
    def get_next_GET(self):
        """Returns the next GET that will occur on the board"""
        ids = str(self.current_post.number)
        digit = ids[-6]
        before = ids[:-5]
        non_dubs_boards = ['b', 'v', 'vg', 'vr']
        if self.board in non_dubs_boards:
             return int(str(int(ids[:-6])+1) + '0'*6)
        kernel = digit * 5 #remember: digits are the kernel
        GET = int(before + kernel)
        if (self.current_post.number > GET): #this occurs if the GET for these digits has already passed
            digit = str(int(str(ids[-6])[-1])+1) #add one because this is the NEXT get
            before = ids[:-6]
            kernel = digit * 6 #REMEMBER: DIGITS ARE THE KERNEL
            GET = int(before + kernel)
        return GET
    
    def post_warning(self):
        """An externally usless function for detecting if current_post and last_post are in an undesirable state"""
        warning = None
        if self.current_post == 0:
            print "Warning: current_post was not set, cannot calculate rate."
            return True
        if self.last_post == 0:
            print "Warning: last_post was not set, cannot calculate rate."
            return True
        if self.last_post.timestamp == self.current_post.timestamp:
            print "Warning: last_post == current_post, cannot calculate rate."
            return True
        return False
    
    def posting_rate(self):
        if not self.post_warning():
            return (self.current_post.number - self.last_post.number)/((self.current_post.timestamp - self.last_post.timestamp)/60.0)   #posts over minutes
        else:
            return 1
    
    def min_until_GET(self):
        """Returns the time in minutes until the next_GET, based on current_post and last_post"""
        if not self.post_warning():
            return (self.next_GET - self.current_post.number)/self.posting_rate()
        else:
            return 10*24*60 #return 10 days in minutes
