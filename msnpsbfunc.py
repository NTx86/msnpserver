from util import *
import random

def sbUSR(conn,data,email,username):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	email = cmdarg[2]
	senttoken = cmdarg[3][:-5]
	usrdata = getuserdata(email)
	with threading.Lock():
		if not senttoken in tokens:
			conn.close()
	del tokens[senttoken]
	with threading.Lock():
		clientsSB[email] = conn
		print(clientsSB)
	conn.send(f"USR {sync} OK {email} {usrdata[3]}\r\n".encode())
	print("auth complete")
	return email,usrdata[3],str(random.randint(1,999999999))
	
def sbCAL(conn,data,email,username,session):
	list = []
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	useremail = cmdarg[2][:-5]
	if session == "empty":
		session = str(random.randint(1,999999999))
	token = str(random.randint(1,999999999))
	print(f"the session is {session}")
	with threading.Lock():
		if not session in sessions:
			sessions[session] = list
		if not email in sessions[session]:
			sessions[session].append(email)
	conn.send(f"CAL {sync} RINGING {session}\r\n".encode())
	print("ringing")
	with threading.Lock():
		tokens[token] = useremail
	with threading.Lock():
		if useremail in clients:
			clients[useremail]['conn'].send(f"RNG {session} {redirect} CKI {token} {email} {username}\r\n".encode())
	print(sessions)
	return session
	#sendusersinvites(conn,sync)
	
def sbMSG(conn,data,email,nickname,session):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	message = data[7 + len(sync):].decode('utf-8')
	with threading.Lock():
		for user in sessions[session]:
			if user != email:
				safesend(clientsSB[user],f"MSG {email} {nickname} " + message)
	
def sbANS(conn,data):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	useremail = cmdarg[2]
	senttoken = cmdarg[3]
	session = cmdarg[4][:-5]
	with threading.Lock():
		if senttoken in tokens:
			email = tokens[senttoken]
			if email in clients:
				nickname = clients[email]['nickname']
			else:
				return "FAIL","FAIL"
		else:
			print(f"ANS FAILED {senttoken}")
			return "FAIL","FAIL"
		del tokens[senttoken]
	with threading.Lock():
		if not email in sessions[session]:
			sessions[session].append(email) #needs to append all the emails
	with threading.Lock():
		clientsSB[email] = conn
		print(clientsSB)
	with threading.Lock():
		for user in sessions[session]:
			for userother in sessions[session]:
				if userother != user:
					safesend(clientsSB[user],f"JOI {userother} {clients[userother]['nickname']}")
	with threading.Lock():
		for user in sessions[session]:
			usercount = 1
			for userall in sessions[session]:
				if userall in clients:
					nickname = clients[userall]['nickname']
					safesend(clientsSB[user],f"IRO {sync} {usercount} {len(sessions[session])} {userall} {nickname}")
					print(f"IRO {sync} {usercount} {len(sessions[session])} {userall} {nickname}\r\n")
					usercount = usercount + 1
	conn.send(f"ANS {sync} OK\r\n".encode())
	print('ANSWERED SWITCHBOARD SERVER')
	print(sessions)
	return session,email,nickname
	
def sbOUT(conn,email,session):
	print(email)
	with threading.Lock():
		if session in sessions:
			if email in sessions[session]:
				sessions[session].remove(email)
		else:
			conn.close()
			return
	sendtoallsession(conn,session,email,f'BYE {email}')
	if len(sessions[session]) == 1:
		del sessions[session]
	conn.close()