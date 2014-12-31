#!/usr/bin/env python2
from GET import GET
import time
from time import sleep
from datetime import timedelta, datetime
import fourch
import tweepy
import ConfigParser
from sys import stdout, stdin

### CONFIG
DAYS_NEW_BOARD_IS_FRESH    = 2     #Days after creation of a board that the bot will still tweet about the new board
MINUTES_GET_IS_SOON        = 45    #Time in minutes before the GET that the bot will try to tweet at
MINUTES_GET_IS_UPON_US     = 5     #Time in minutes before the GET that it is basically occuring already
HOURS_HUMAN_TWEET_IS_RELEVANT = 1   #The bot will not tweet about a GET if a human has tweeted about it within this many hours
MODE = "total"  #still debugging, can't afford push because it takes to long

GET_TEXT = "{get_name} coming up on /{board}/ in about {time_until} minutes (~{posts_to_go} posts)."
NEW_BOARD_TEXT = "New board: /{board}/ \nGet all the early GETs!"


#OAUTH STUFF
config = ConfigParser.ConfigParser()
config.read("oauth.conf")
CONSUMER_KEY    = config.get('Api', 'ApiKey')
CONSUMER_SECRET = config.get('Api', 'ApiSecret')
ACCESS_KEY      = config.get('Access', 'AccessToken')
ACCESS_SECRET   = config.get('Access', 'AccessSecret')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.secure = True
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
twitter = tweepy.API(auth)



### DEFINITIONS BEFORE MAIN LOOP
#detect new boards and tweet about them
def update_boards(boards):    #update list of boardnames, and tweet about new ones
    try:
        new_listed_boards = fourch.boards()
    except Exception:
        print "Error getting boards from 4chan. Using old boards instead."
        return boards
    new_boards = [new_listed_board.board    for new_listed_board in new_listed_boards]
    if boards != new_boards:    #If there is a new board...
        try:
            with open('.boards_cache.txt', 'r') as f:
                last_update_timestamp = f.readline()    #Get last time boards were updated
        except IOError:
            open('.boards_cache.txt', 'w').close()  #Create file if it doesn't exist
            last_update_timestamp = 0 
        if (time.time() - float(last_update_timestamp)) / 86400 < DAYS_NEW_BOARD_IS_FRESH:    #If the boards were updated recently enough...
            for new_board in new_boards:
                if not new_board in boards:
                    print "New board: "+new_board
                    #print NEW_BOARD_TEXT.format(board=new_board)
                    twitter.update_status(NEW_BOARD_TEXT.format(board=new_board))
        boards = new_boards    #Update boards
    with open('.boards_cache.txt', 'w') as f:
        f.write(str(time.time())+'\n')
        for listed_board in boards:
            f.write(listed_board+'\n')
    return boards

#Check if someone has tweeted about the GET
def get_tweeted(board):
    timeline = twitter.user_timeline(count=20)
    for status in timeline:
        if '/'+board.board+'/' in status.text:   #Do not tweet if a human has mentioned the board in the past hour
            if (datetime.now() - status.created_at).days*24 < HOURS_HUMAN_TWEET_IS_RELEVANT:
                return True
    #If we are here, the humans have not tweeted
    return False

#Returns the number of repeating digits at the end of a number
#Translated from my original JS algorithm
def GET_value(ID):  
    IDs = str(ID)   
    GETValue = 1
    digit = IDs[-1]
    i = len(IDs)
    while (i>1):
        if (digit == IDs[i-2]):
            GETValue += 1
        else:
            break
        i -= 1
    return GETValue

#Returns the name of a GET
def GET_name(GET):
    if str(GET)[-1] == 9:   #Change 9s to 0s, e.g. 1999999 becomes 2000000
        GET += 1
    GETs = str(GET)
    if GETs[-6] == GETs[-1] == 0:   #Change clear GETs to the M value, e.g. 2000000 becomes 2M GET instead of just sexts
        return GETs[:-6]+"M GET"
    GETValue = GET_value(GET)
    GET_names_dict = {
        5: 'quints',    #this one should never be printed
        6: 'sexts',
        7: 'septs',
        8: 'octs',
        9: 'nons',
        10: 'Fuggin huge GET'
    }
    return GET_names_dict[GETValue]



### STARTUP CODE BEFORE MAIN LOOP
try:
    open('.boards_cache.txt', 'r').close()
except IOError:
    open('.boards_cache.txt', 'w').close()  #creates the file if it doesnt exist

with open('.boards_cache.txt', 'ra') as f:    #load cached boardnames, so I can detect which ones are new.
    l = f.read().split()
    timestamp = l[0]    #first line is the time boardnames were saved
    boardnames = l[1:]  #the rest are the boards

#Initialize list of GET classes
stdout.write('Initializing boards... ')
stdout.flush()
boards = []
for boardname in boardnames:
    stdout.write(boardname+' ')
    stdout.flush()
    retry = True
    retries = 0
    while retry:
        try:
            boards.append(GET(boardname, "push"))
            retry = False
        except ValueError:  #fourch throws ValueError whenever 4chan sends non-json response
            retry = True
            if retries >= 4:    #stop retrying after 5 times
                print "Error even after retrying 5 times."
                raise
            if retries == 0:
                retries += 1
                print "\nError initializing board. Retrying..."
        except:
            raise
stdout.write('done!\n')
stdout.flush()



### MAIN LOOP
while True:
    print 'Starting loop!'
    print 'Updating boardnames...'
    boardnames = update_boards(boardnames)
    if MODE == 'push':  #push requires that it sleeps right now
        print 'Sleeping 10 minutes...'
        sleep(10*60)
    for board in boards:
        retry = True
        retries = 0
        while retry:
            try:
                if MODE == 'push':
                    board.push_posts()
                elif MODE == 'total':
                    board.update_posts()
                else:
                    print 'Warning: unknown time estimation mode.'
                retry = False
            except ValueError:  #fourch throws ValueError whenever 4chan sends non-json response
                retry = True
                if retries >= 4: #stop retrying after 5 times
                    print "Error even after retrying 5 times."
                    raise
                if retries == 0:
                    retries += 1
                    print "Error getting lastest posts from 4chan. Retrying..."
            except:
                raise
        next_GET = board.get_next_GET()
        if board.next_GET != next_GET:  #check if the GET is over
            board.next_GET = next_GET
        posts_to_go = board.next_GET - board.current_post.number
        posts_to_go = round(posts_to_go, 1-len(str(posts_to_go)))   #round to the first digit
        min_until = board.min_until_GET()
        print "Time until /"+board.board+'/ '+GET_name(board.next_GET)+": ", str(timedelta(minutes=round(min_until)))
        if min_until < MINUTES_GET_IS_SOON and min_until > MINUTES_GET_IS_UPON_US:
            tweeted = -1    #"NULL" value
            while tweeted == -1:
                try:
                    tweeted = get_tweeted(board)
                except tweepy.error.TweepError as TError:
                    if 'Rate limit exceeded' in TError[0][0]['message']:
                        print "Rate limit exceeded when checking if the GET has been tweeted about. Retrying in 15 minutes..."
                        sleep(60*15)
                    else:
                        raise
                except:
                    raise
            if tweeted == False:
                print 'Tweeting!'
                msg = GET_TEXT.format(board=board.board, time_until=int(min_until), get_name=GET_name(board.next_GET), posts_to_go=int(posts_to_go)).capitalize()
                twitter.update_status(msg)  #could add another tweepy error handler
                print msg
            else:
                print 'Already tweeted.'
        sleep(2)    #to meet 4chan API timing standards
    if MODE == 'total': #with total, it can sleep after
        print 'Sleeping 10 minutes...'
        sleep(10*60)
