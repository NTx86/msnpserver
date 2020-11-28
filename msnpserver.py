import socket
import mysql.connector
import threading
import random
import config as cfg


clients = {}
clients_lock = threading.Lock()
tokens = {}
tokens_lock = threading.Lock()

FL = 0
AL = 1
BL = 2
RL = 3

mydb = cfg.mydb
mycursor = mydb.cursor()
redirect = cfg.redirect

def safesend(socket,data):
	try:
		socket.send(data)
	except Exception as e:
		print("socket send fail")

def getuserdata(email):
	sqlarg = (email, )
	sql = "SELECT * FROM users WHERE email = %s"
	mycursor.execute(sql,sqlarg)
	#print(mycursor.fetchone())
	return mycursor.fetchone()
	
def changenickname(nickname,email):
	sqlarg = (nickname,email)
	sql = "UPDATE users SET nickname = %s WHERE email = %s"
	mycursor.execute(sql,sqlarg)
	#sqlarg = (nickname,email)
	sql = "UPDATE friendlist SET nickname = %s WHERE emailfriend = %s"
	mycursor.execute(sql,sqlarg)
	#return mycursor.fetchone()
	
def changelocalnickname(nickname,email,useremail):
	sqlarg = (nickname,email,useremail)
	sql = "UPDATE friendlist SET nickname = %s WHERE email = %s AND emailfriend = %s"
	mycursor.execute(sql,sqlarg)
	return nickname
	#return mycursor.fetchone()
	
def incrementversion(email):
	sqlarg = (email, )
	sql = "UPDATE users SET version = version+1 WHERE email = %s"
	mycursor.execute(sql,sqlarg)
	
def changeprivacy(privacy,email):
	if privacy == "A": 
		privacy = 0
	else: 
		privacy = 1
	sqlarg = (privacy,email)
	sql = "UPDATE users SET privacy = %s WHERE email = %s"
	mycursor.execute(sql,sqlarg)
	#return mycursor.fetchone()
	
def convertlisttoint(list):
	if list == "FL": return 0
	if list == "AL": return 1
	if list == "BL": return 2
	if list == "RL": return 3
	return 0
	
def convertlisttostr(list):
	if list == 0: return "FL"
	if list == 1: return "AL"
	if list == 2: return "BL"
	if list == 3: return "RL"
	return "FL"
	
def addtolist(account,list,email):
	#sqlarg = (account,email,email,convertlisttoint(list))
	#sql = "INSERT INTO friendlist (email,emailfriend,nickname,list) VALUES(%s, %s, %s, %s)"
	#mycursor.execute(sql,sqlarg)
	sqlarg = (email,account,account,convertlisttoint(list))
	sql = "INSERT INTO friendlist (email,emailfriend,nickname,list) VALUES(%s, %s, %s, %s)"
	mycursor.execute(sql,sqlarg)
	
def deletelist(account,list,email):
	#sqlarg = (account,email,email,convertlisttoint(list))
	#sql = "INSERT INTO friendlist (email,emailfriend,nickname,list) VALUES(%s, %s, %s, %s)"
	#mycursor.execute(sql,sqlarg)
	sqlarg = (email,account,convertlisttoint(list))
	sql = "DELETE FROM friendlist WHERE email = %s AND emailfriend = %s AND list = %s"
	mycursor.execute(sql,sqlarg)
	
def sendlist(conn,list,sync,usergroup,email,version):
	usercounting = 1
	#if list != FL:
	#	usergroup = ""
	sqlarg = (email, list)
	sqlcmd = "SELECT * FROM friendlist WHERE email = %s AND list = %s"
	mycursor.execute(sqlcmd,sqlarg)
	friendlist = mycursor.fetchall()
	usercount = mycursor.rowcount

	for friend in friendlist:
		if friend[4] == list:
			conn.send(f"LST {sync} {convertlisttostr(list)} {version} {usercounting} {usercount} {friend[2]} {friend[3]} {usergroup}\r\n".encode()) #the usergroup space could cause problems for some clients
			usercounting = usercounting + 1
	if usercounting == 1:
		conn.send(f"LST {sync} {convertlisttostr(list)} {version} 0 0\r\n".encode())
		
def sendlist10(conn,list,sync,usergroup,email,version):
	usercounting = 1
	sqlarg = (email, list)
	sqlcmd = "SELECT * FROM friendlist WHERE email = %s AND list = %s"
	mycursor.execute(sqlcmd,sqlarg)
	friendlist = mycursor.fetchall()
	usercount = mycursor.rowcount
	
	for friend in friendlist:
		if friend[4] == list:
			conn.send(f"LST N={friend[2]} F={friend[3]} C=996b128c-b60e-406f-9067-7c695fd22a88\r\n".encode()) #more stubs
			usercounting = usercounting + 1
		
def getallfriends(email):
	sqlarg = (email, )
	sqlcmd = "SELECT * FROM friendlist WHERE email = %s AND list = 0"
	mycursor.execute(sqlcmd,sqlarg)
	friendlist = mycursor.fetchall()
	return friendlist
		
def sendoutstatuses(conn,sync,email):
	#sqlarg = (email, )
	#sqlcmd = "SELECT * FROM friendlist WHERE email = %s AND list = 0"
	#mycursor.execute(sqlcmd,sqlarg)
	friendlist = getallfriends(email)
	
	with clients_lock:
		for friend in friendlist:
			if friend[2] in clients:
				conn.send(f"ILN {sync} {clients[friend[2]]['status']} {friend[2]} {friend[3]}\r\n".encode())
			else:
				conn.send(f"ILN {sync} FLN {friend[2]} {friend[3]}\r\n".encode())
		
def sendtoallfriends(email,data):
	with clients_lock:
		for x in getallfriends(email):
			if x[2] in clients:
				#clients[x[2]]['conn'].send(data)
				print(f"{email} {data}")
				safesend(clients[x[2]]['conn'],data)

def sendover(conn,sync,email,version,msnver,nickname):
	#version = '37'
	usrdata = getuserdata(email)
	privacy = usrdata[4]
	privacymsg = usrdata[5]
	
	if privacy == 0: 
		privacy = "A" 
	else: 
		privacy = "N"
	if privacymsg == 0: 
		privacymsg = "AL" 
	else: 
		privacymsg = "BL"
	usergroup = ""
	if msnver <= 9:
		conn.send(f"GTC {sync} {version} {privacy}\r\n".encode())
		conn.send(f"BLP {sync} {version} {privacymsg}\r\n".encode())
	else:
		conn.send(f"GTC {privacy}\r\n".encode())
		conn.send(f"BLP {privacymsg}\r\n".encode())
		conn.send(f"PRP MFN {nickname}\r\n".encode())
	if msnver >= 10:
		conn.send(f"LSG contacts bf9a6841-9d78-4b64-b056-3e80ee0dd47b\r\n".encode()) #2nd is total count
		print("msnp10 stubby stub stub")
		usergroup = 0
	if msnver >= 7:
		conn.send(f"LSG {sync} {version} 1 1 0 Other%20Contacts 0\r\n".encode()) #2nd is total count
		usergroup = 0
	
	if msnver < 10:
		sendlist(conn,FL,sync,usergroup,email,version)
		sendlist(conn,AL,sync,"",email,version)
		sendlist(conn,BL,sync,"",email,version)
		sendlist(conn,RL,sync,"",email,version)
	else:
		sendlist10(conn,FL,sync,usergroup,email,version)
	sendoutstatuses(conn,sync,email)
	
	
def cmdVER(conn,data):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	print(str(data)[8:])
	if cmdarg[2] == "MSNP2":
		conn.send(f"VER {sync} MSNP2 CVR0\r\n".encode())
		print("msnp2 mode")
		return 2
	elif cmdarg[2] == "MSNP3":
		conn.send(f"VER {sync} MSNP3 CVR0\r\n".encode())
		print("msnp3 mode")
		return 3
	elif cmdarg[2] == "MSNP4":
		conn.send(f"VER {sync} MSNP4 CVR0\r\n".encode())
		print("msnp4 mode")
		return 4
	elif cmdarg[2] == "MSNP5":
		conn.send(f"VER {sync} MSNP5 CVR0\r\n".encode())
		print("msnp5 mode")
		return 5
	elif cmdarg[2] == "MSNP6":
		conn.send(f"VER {sync} MSNP6 CVR0\r\n".encode())
		print("msnp6 mode")
		return 6
	elif cmdarg[2] == "MSNP7":
		conn.send(f"VER {sync} MSNP7 CVR0\r\n".encode())
		print("msnp7 mode")
		return 7
	elif cmdarg[2] == "MSNP8":
		conn.send(f"VER {sync} MSNP8 CVR0\r\n".encode())
		print("msnp8 mode")
		return 8
	elif cmdarg[2] == "MSNP9":
		conn.send(f"VER {sync} MSNP9 CVR0\r\n".encode())
		print("msnp9 mode")
		return 9
	elif cmdarg[2] == "MSNP10":
		conn.send(f"VER {sync} MSNP10 CVR0\r\n".encode())
		print("msnp10 mode")
		return 10
	elif cmdarg[2] == "MSNP11":
		conn.send(f"VER {sync} MSNP10 CVR0\r\n".encode())
		print("msnp10 mode")
		return 10
	elif cmdarg[2] == "MSNP12":
		conn.send(f"VER {sync} MSNP10 CVR0\r\n".encode())
		print("msnp10 mode")
		return 10
	else:
		conn.send(f"VER {sync} MSNP2 CVR0\r\n".encode())
		print("msnp2 mode")
		return 2
		
	
def cmdUSR(conn,data,email,msnver):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	if cmdarg[2] == 'MD5':
		if cmdarg[3] == "I":
			email = str(cmdarg[4][:-5]).lower()
			usrdata = getuserdata(email)
			print(usrdata)
			if usrdata:
				conn.send(f"USR {sync} MD5 S 1013928519.693957190\r\n".encode())
				print("sent a challenge")
				return email,usrdata[6],''
			else:
				conn.send(f"911 {sync}\r\n".encode())
				return 'FAIL',0,''
		if cmdarg[3] == "S":
			usrdata = getuserdata(email)
			passwordmd5sent = cmdarg[4][:-5]
			passwordmd5 = usrdata[2]
			nickname = usrdata[3]
			if not usrdata:
				conn.send(f"911 {sync}\r\n".encode())
				return 'FAIL',0,''
			if passwordmd5sent != passwordmd5:
				conn.send(f"911 {sync}\r\n".encode())
				return 'FAIL',0,''
			with clients_lock:
				clients[email] = dict()
				clients[email]['conn'] = conn
				clients[email]['status'] = 'FLN'
				clients[email]['nickname'] = nickname
				clients[email]['authkey'] = '0'
			conn.send(f"USR {sync} OK {email} {nickname}\r\n".encode())
			#conn.send(notif)
			print("auth complete")
			incrementversion(email)
			return email,usrdata[6],nickname
	elif cmdarg[2] == 'TWN':
		if cmdarg[3] == "I":
			email = str(cmdarg[4][:-5])
			conn.send(f"USR 6 TWN S ct=1312946236,rver=6.1.6206.0,wp=FS_40SEC_0_COMPACT,lc=1033,id=507,ru=http:%2F%2Fmessenger.msn.com,tw=0,kpp=1,kv=4,ver=2.1.6000.1,rn=1lgjBfIL,tpf=b0735e3a873dfb5e75054465196398e0\r\n".encode())
			print("sent a challenge")
			usrdata = getuserdata(email)
			return email,usrdata[6],''
		if cmdarg[3] == "S":
			usrdata = getuserdata(email)
			passwordmd5sent = cmdarg[4][:-5]
			passwordmd5 = usrdata[2]
			nickname = usrdata[3]
			if not usrdata:
				conn.send(f"911 {sync}\r\n".encode())
				return 'FAIL',0,''
			with clients_lock:
				clients[email] = dict()
				clients[email]['conn'] = conn
				clients[email]['status'] = 'FLN'
				clients[email]['nickname'] = nickname
				clients[email]['authkey'] = '0'
			if msnver == 9:
				conn.send(f"USR {sync} OK {email} {nickname} 1 0\r\n".encode())
			elif msnver >=10:
				conn.send(f"USR {sync} OK {email} 1 0\r\n".encode())
			else:
				conn.send(f"USR {sync} OK {email} {nickname}\r\n".encode())
			#conn.send(notif)
			print("auth complete")
			incrementversion(email)
			return email,usrdata[6],nickname

def dispatchINF(conn,data):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1][:-5]
	conn.send(f"INF {sync} MD5\r\n".encode())
	print(f"sent INF {sync} MD5")
	
def cmdSYN(conn,data,version,email,msnver,nickname):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	#msnver = cmdarg[2][:-5]
	conn.send(f"SYN {sync} {version}\r\n".encode())
	#if msnver != version:
	sendover(conn,sync,email,version,msnver,nickname)
	
def cmdCHG(conn,data,status,msnver,email,username):
	cmdarg = data.split(' ')
	sync = cmdarg[1]
	status = cmdarg[2]
	print("status is "+status)
	conn.send((data+"\r\n").encode())
	with clients_lock:
		clients[email]['status'] = status
	sendtoallfriends(email,f"ILN {sync} {status} {email} {username}\r\n".encode())
	return status
	
def cmdCVR(conn,data,msnver):
	if msnver >= 8:
		cmdarg = data.split(' ')
		sync = cmdarg[1]
		conn.send(f"CVR {sync} 6.2.0208 6.2.0208 6.2.0208 https://escargot.log1p.xyz https://escargot.log1p.xyz\r\n".encode())
		print("CVR SENT")
	
def cmdREA(conn,data,email,username):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	useremail = cmdarg[2]
	usernamechg = cmdarg[3][:-5]
	if useremail == email:
		changenickname(usernamechg,email)
		sendtoallfriends(email,f"REA {sync} 19 {useremail} {usernamechg}\r\n".encode())
	else:
		with clients_lock:
			if useremail in clients:
				usernamechg = usernamechg#clients[useremail]['nickname']
			else:
				usernamechg = useremail
		changelocalnickname(usernamechg,email,useremail)
	conn.send(f"REA {sync} 19 {useremail} {usernamechg}\r\n".encode())
	print(f"REA {sync} 19 {useremail} {usernamechg}")
	usernamechg = username
	incrementversion(email)
	return usernamechg
	
def cmdGTC(conn,data,email,version):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	status = cmdarg[2][:-5]
	changeprivacy(status,email)
	conn.send(f"GTC {sync} {version} {status}\r\n".encode())
	incrementversion(email)
	
def cmdXFR(conn,data,email):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	key = str(random.randint(1,999999999))
	with clients_lock:
		tokens[key] = email
	print("XFR redirecting to switchboard")
	conn.send(f"XFR {sync} SB {redirect} CKI {key}\r\n".encode())
	
def cmdURL(conn,data):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	conn.send(f"URL {sync} /unused1 /unused2\r\n".encode())
	
def cmdADD(conn,data,email,version):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	listtype = cmdarg[2]
	account = cmdarg[3].lower()
	account2 = cmdarg[4][:-5].lower()
	addtolist(account,listtype,email)
	conn.send(f"ADD {sync} {listtype} {version} {account} {account2}\r\n".encode())
	print(f"ADD {sync} {listtype} {version} {account} {account2}")
	incrementversion(email)
	
def cmdREM(conn,data,email,version):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	listtype = cmdarg[2]
	account = cmdarg[3][:-5].lower()
	deletelist(account,listtype,email)
	conn.send(f"REM {sync} {listtype} {version} {account}\r\n".encode())
	print(f"REM {sync} {listtype} {version} {account}")
	incrementversion(email)


def connected(conn,addr):
	email = "blank@hotmail.com"
	username = "MSNUser"
	status = "NLN"
	version = 0
	msnver = 2
	try:
		while 1:
			data = conn.recv(BUFFER_SIZE)
			if not data: break
			#print("received data:", data)
			cmds = data.decode('utf-8').splitlines()
			for command in cmds:
				cmd = command[0:3]
				data = (command+'\r\n').encode() #legacy code compatibility
				ndata = command
				print(ndata)
				if cmd == "INF":
					dispatchINF(conn,data)
					continue
				if cmd == "VER":
					msnver = cmdVER(conn,data)
					continue
				if cmd == "USR":
					email,version,username = cmdUSR(conn,data,email,msnver)
					if email == "FAIL":
						break
					print(username)
					continue
				if cmd == "SYN":
					cmdSYN(conn,data,version,email,msnver,username)
					continue
				if cmd == "CHG":
					status = cmdCHG(conn,ndata,status,msnver,email,username)
					continue
				if cmd == "OUT":
					#sendtoallfriends(email,f"ILN 1 FLN {email} {username}\r\n".encode())
					#del clients[email]
					conn.close()
					break
				if cmd == "CVR":
					cmdCVR(conn,ndata,msnver) 
					continue
				if cmd == "REA":
					username = cmdREA(conn,data,email,username)
					continue
				if cmd == "GTC":
					cmdGTC(conn,data,email,version)
					continue
				if cmd == "XFR":
					cmdXFR(conn,data,email) 
					continue
				if cmd == "URL":
					cmdURL(conn,data) 
					continue
				if cmd == "ADD":
					cmdADD(conn,data,email,version)
					continue
				if cmd == "REM":
					cmdREM(conn,data,email,version) 
					continue
			#conn.close()
			#break
			#conn.send(data)  # echo
		conn.close()
	except socket.error as e:
		sendtoallfriends(email,f"ILN 1 FLN {email} {username}\r\n".encode())
		if email in clients:
			del clients[email]
		conn.close()
	finally:
		sendtoallfriends(email,f"ILN 1 FLN {email} {username}\r\n".encode())
		if email in clients:
			del clients[email]
		conn.close()
				
#============================================================================================
#START OF THE SWITCHBOARD SERVER
#todo split stuff into more readable functions
#============================================================================================
mymessage = "MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\nhello you are an sucker because i am a switchboard server"
mymessage2 = "MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\n\r\nlmao just shut up"
mytyping = "MIME-Version: 1.0\r\nContent-Type: text/x-msmsgscontrol\r\nTypingUser: friend@hotmail.com\r\n\r\n\r\n"		
clientsSB = {}
clientsSB_lock = threading.Lock()
sessions = {}
sessions_lock = threading.Lock()

def sendtoallsession(conn,session,email,data): #leave email blank to send to all including you
	with sessions_lock:
		for user in sessions[session]:
			if user != email:
				safesend(clientsSB[user],data)
				print(f"{user} {data}")
	

def sbUSR(conn,data,email,username):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	email = cmdarg[2]
	senttoken = cmdarg[3][:-5]
	usrdata = getuserdata(email)
	with tokens_lock:
		if not senttoken in tokens:
			conn.close()
	del tokens[senttoken]
	with clientsSB_lock:
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
	with sessions_lock:
		if not session in sessions:
			sessions[session] = list
		if not email in sessions[session]:
			sessions[session].append(email)
	conn.send(f"CAL {sync} RINGING {session}\r\n".encode())
	print("ringing")
	with tokens_lock:
		tokens[token] = useremail
	with clients_lock:
		if useremail in clients:
			clients[useremail]['conn'].send(f"RNG {session} {redirect} CKI {token} {email} {username}\r\n".encode())
	print(sessions)
	return session
	#sendusersinvites(conn,sync)
	
def sbMSG(conn,data,email,nickname,session):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	message = data[7 + len(sync):]
	with clientsSB_lock:
		for user in sessions[session]:
			if user != email:
				safesend(clientsSB[user],f"MSG {email} {nickname} ".encode() + message)
	
def sbANS(conn,data):
	cmdarg = str(data).split(' ')
	sync = cmdarg[1]
	useremail = cmdarg[2]
	senttoken = cmdarg[3]
	session = cmdarg[4][:-5]
	with tokens_lock:
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
	with sessions_lock:
		if not email in sessions[session]:
			sessions[session].append(email) #needs to append all the emails
	with clientsSB_lock:
		clientsSB[email] = conn
		print(clientsSB)
	with clientsSB_lock:
		for user in sessions[session]:
			safesend(clientsSB[user],f"JOI {email} {nickname}\r\n".encode())
	with sessions_lock:
		for user in sessions[session]:
			usercount = 1
			for userall in sessions[session]:
				if userall in clients:
					nickname = clients[userall]['nickname']
					safesend(clientsSB[user],f"IRO {sync} {usercount} {len(sessions[session])} {userall} {nickname}\r\n".encode())
					print(f"IRO {sync} {usercount} {len(sessions[session])} {userall} {nickname}\r\n")
					usercount = usercount + 1
	conn.send(f"ANS {sync} OK\r\n".encode())
	print('ANSWERED SWITCHBOARD SERVER')
	print(sessions)
	return session,email,nickname
	
def sbOUT(conn,email,session):
	print(email)
	with sessions_lock:
		if session in sessions:
			if email in sessions[session]:
				sessions[session].remove(email)
		else:
			conn.close()
			return
	sendtoallsession(conn,session,email,f'BYE {email}\r\n'.encode())
	if len(sessions[session]) == 1:
		del sessions[session]
	conn.close()
	
def connectedSB(conn, addr):
	email = "blank@hotmail.com"
	nickname = "MSNUser"
	status = "NLN"
	session = 'empty'
	closing = False
	try:
		while 1:
			data = conn.recv(BUFFER_SIZE)
			if not data: break
			print("received data:", str(data))
			cmd = data[0:3].decode()
			if cmd == "USR":
				email,nickname,session = sbUSR(conn,data,email,nickname)
				continue
			if cmd == "CAL":
				session = sbCAL(conn,data,email,nickname,session)
				continue
			if cmd == "OUT":
				sbOUT(conn,email,session)
				closing = True
				break
			if cmd == "MSG":
				sbMSG(conn,data,email,nickname,session)
				continue
			if cmd == "ANS":
				session,email,nickname = sbANS(conn,data)
				if session == "FAIL": break
	except socket.error as e:
		print(e)
		if closing == False: sbOUT(conn,email,session)
	finally:
		if closing == False: sbOUT(conn,email,session)
		
def startlisteningSB():
	while 1:
		TCP_IP = '0.0.0.0'
		TCP_PORT = cfg.portsb
		BUFFER_SIZE = 1024
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((TCP_IP, TCP_PORT))
		s.listen(1)

		conn, addr = s.accept()
		print('Connection address:', addr)
		thread = threading.Thread(target=connectedSB,args=(conn, addr))
		thread.start()
		#connectedSB()

SBthread = threading.Thread(target=startlisteningSB)
SBthread.start()

while 1:
	TCP_IP = '0.0.0.0'
	TCP_PORT = cfg.portnf
	BUFFER_SIZE = 1024

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((TCP_IP, TCP_PORT))
	print(f"start listen {TCP_IP} {TCP_PORT}")
	s.listen(1)

	conn, addr = s.accept()
	print('Connection address:', addr)
	thread = threading.Thread(target=connected,args=(conn, addr))
	thread.start()
