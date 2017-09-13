#!/usr/bin/python
import json
import datetime
import httplib

import socket
import time
import os
import traceback
import sys


from persistent_queue import PersistentQueue

FPLAYER_ADDR="192.168.0.19"
FPLAYER_PORT=54243

index_name=datetime.datetime.now().strftime("pi-events-%Y.%m.%d")
esConnection=None
def getEsConnection():
	global esConnection
	if not esConnection:
		esConnection=httplib.HTTPConnection("server1",9200)
	return esConnection
sessions_queue=PersistentQueue("Session.queue")



def index_doc(doc,doctype,docid=None):
	doc['ts']=datetime.datetime.now().isoformat()
	if docid:
		url="%s/%s/%s"%(index_name,doctype,docid)
	else:
		url="%s/%s"%(index_name,doctype)

	indexing_req=getEsConnection().request("POST", url, json.dumps(doc))
	resp=esConnection.getresponse()
	rc=resp.status
	if (rc/100)!=2:
		raise Exception("unable to index document. URL=%s rc=%s error=%s"%(url,rc,resp.read()))

def test_port(addr,port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	result=sock.connect_ex((addr,port))
	sock.close()
	return not result

def queuefile(session_id):
	return "sessions_queue/"+str(session_id)+'.session'

def send_queued_sessions():
	while sessions_queue.count():
		queued_session_id=sessions_queue.peek()
		queued_file_name=queuefile(queued_session_id)
		queued_session_doc=None
		try:
			with open(queued_file_name,'r') as queued_file:
				queued_session_doc=json.load(queued_file)
		except Exception as e:
			print("ERROR : unable to find session data. Id=%s File+%s Exception=%s"%(queued_session_id,queued_file_name,e))

		if queued_session_doc:
			index_doc(queued_session_doc,'psession',queued_session_id)
		try:
			os.remove(queued_file_name)
		except:
			pass
		sessions_queue.delete()
	

def store_queued_session_content(player_session, session_id):
	with open(queuefile(session_id),'w') as queued_file:
		json.dump(player_session,queued_file)


player_session=None
try:
	send_queued_sessions()
except:
	traceback.print_exc()
	esConnection=None
while True:
	try:
		player_used=test_port(FPLAYER_ADDR,FPLAYER_PORT)
		print(player_used)
		if player_used:
			curts=datetime.datetime.now().isoformat()
			if not player_session:
				# NEW SESSION
				session_id=str(int(time.time()))
				player_session=dict()
				player_session['start_ts']=curts
				sessions_queue.push(session_id)
			# we do not know when it will end, but let's record temporarily current time in case we crash
			player_session['end']=curts
			# and let's persist the document for later insertion
			store_queued_session_content(player_session,session_id)
		else:
			if player_session:
				# END OF A SESSION
				store_queued_session_content(player_session,session_id)
				player_session=None
			player_session=None
			send_queued_sessions()
	except Exception as e:
		print("Error in main loop : ")
		traceback.print_exc()
		esConnection=None
		
	time.sleep(1)

