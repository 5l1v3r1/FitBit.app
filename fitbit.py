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

import sqlite3 as sqlite3

#####################################################################################################################################

home_directory = "/Applications/FitBit.app/"

#####################################################################################################################################

class DatabaseManager(object):
	def __init__(self, db):
		self.conn = sqlite3.connect(db,isolation_level=None)
		self.cursor = self.conn.cursor()
		self._createTable()
	
	def close(self):
		self.cursor.close()
		self.conn.close()
	
	def _createTable(self):
		self.cursor.execute("CREATE TABLE IF NOT EXISTS session(id INTEGER PRIMARY KEY,start_stamp VARCHAR(26),end_stamp VARCHAR(26),sent INTEGER DEFAULT 0,sent_stamp VARCHAR(26))")
		
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
		if not len(config.get('config',option)):
			print option + " not set."
			exit()
		else:
			return config.get('config',option)
	else:
		print "Missing option " + option + "\nAborting."
		exit()
		
#####################################################################################################################################
# Log Activiety
#####################################################################################################################################

def LogFitBitSession(session):
	duration = CalcDuration(session)
	if duration:
		authd_client = fitbit.Fitbit(GetConfig('consumer_key'),GetConfig('consumer_secret'), resource_owner_key=GetConfig('user_key'), resource_owner_secret=GetConfig('user_secret'))
		if authd_client:
			authd_client.sleep()
			ret = authd_client.log_activity(
				{
					'activityId':'16030',
					'manualCalories':'0',
					'startTime':duration['startTime'],
					'durationMillis':duration['millis'],
					'date':duration['date']
				})
			if int(ret['activityLog']['activityId']) == 16030:
				return True
	return False

#####################################################################################################################################
# Log it to current session
#####################################################################################################################################

db = DatabaseManager(home_directory + "fitbit_sessions.db")
	
db.cursor.execute("SELECT MAX(id) FROM session WHERE end_stamp is NULL AND sent=0")
try:
	row = db.cursor.fetchone()[0]
except:
	row = False
	
if row:
	db.cursor.execute("UPDATE session SET end_stamp=? WHERE id = ?",(str(datetime.datetime.now()),row))
else:
	db.cursor.execute("INSERT INTO session (start_stamp) values(?)",(str(datetime.datetime.now()),))

#####################################################################################################################################
# 'Attempt' to dequeue actively events.
#####################################################################################################################################

db.cursor.execute("SELECT id,start_stamp,end_stamp FROM session WHERE (start_stamp NOT NULL AND end_stamp NOT NULL) AND sent=0")
for queue in db.cursor.fetchall():
	if LogFitBitSession({'session_start': queue[1],'session_end': queue[2]}) is True:
		db.cursor.execute("UPDATE session SET sent=1,sent_stamp=? WHERE id = ?",(str(datetime.datetime.now()),str(queue[0])))
		
#####################################################################################################################################
# The world just ended....
#####################################################################################################################################
db.close()