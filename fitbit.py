#!/usr/bin/python

#####################################################################################################################################

import fitbit

#####################################################################################################################################

import datetime
import os.path
from os import listdir
import json

#####################################################################################################################################

import ConfigParser

#####################################################################################################################################
home_directory = "/Applications/FitBit.app/"
queue_directory = home_directory + 'queue/'
current_session = home_directory + 'current_session.json'

#####################################################################################################################################

def QueueItem(item):
	items = ReadSession(current_session)
	if not items:
		items = {}
	for key in item:
		items[key] = item[key]
	with open(current_session, 'w') as f:
		json.dump(items, f)
		
#####################################################################################################################################

def ReadSession(session_file):
	if os.path.isfile(session_file):
		with open(session_file, 'r') as f:
			session = json.load(f)
		if type(session) is dict:
			return session
	return None

#####################################################################################################################################

def CalcDuration(session):
	start = datetime.datetime.strptime(session['session_start'], "%Y-%m-%d %H:%M:%S.%f")
	end = datetime.datetime.strptime(session['session_end'], "%Y-%m-%d %H:%M:%S.%f")
	c = end - start
	if c.total_seconds() > 0:
		duration = {}
		duration['millis'] = str(int(c.total_seconds()*1000))
		duration['date'] = str(start.strftime("%Y-%m-%d"))
		duration['startTime'] = str(start.strftime("%H:%M"))
		return duration
	return None

#####################################################################################################################################

def GetConfig(option):
	config = ConfigParser.ConfigParser()
	
	if not len(config.read(home_directory + 'config.ini')):
		print "Can't read config.ini.... \nAborting."
		exit()
	
	if config.has_option('config',option):
		return config.get('config',option)
	else:
		print "Missing option " + option + "\nAborting."
		exit()
		
#####################################################################################################################################

def LogFitBitSession(session):
	duration = CalcDuration(session)
	if duration:
		authd_client = fitbit.Fitbit(GetConfig('consumer_key'),GetConfig('consumer_secret'), resource_owner_key=GetConfig('user_key'), resource_owner_secret=GetConfig('user_secret'))
		if authd_client:
			authd_client.sleep()
			ret = authd_client.log_activity({'activityId':'16030', 'manualCalories':'0', 'startTime':duration['startTime'], 'durationMillis':duration['millis'], 'date':duration['date']})
			if int(ret['activityLog']['activityId']) == 16030:
				return True
	return False

#####################################################################################################################################
# Log it to current session

if os.path.isfile(current_session):
	QueueItem({'session_end': str(datetime.datetime.now())})
	#####################################################################################################################################
	# Move File to queue incase LogFitBitSession gets a web exception , dont want it blocking future events and fudging activey length.
	if os.path.isfile(current_session):
		os.rename(current_session, queue_directory + 'session-'+str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))+'.json')
else:
	QueueItem({'session_start': str(datetime.datetime.now())})

#####################################################################################################################################
# 'Attempt' to dequeue actively events.

queue_files = [ f for f in listdir(queue_directory) if os.path.isfile(os.path.join(queue_directory,f)) and f.endswith('.json')]

for queue_file in queue_files:
	session = ReadSession(queue_directory + queue_file)
	if session:
		if LogFitBitSession(session) is True:
			os.unlink(queue_directory + queue_file)

#####################################################################################################################################
# The world just ended....
#####################################################################################################################################