import socket
import threading
import uuid
import config as cfg

clients = {}
tokens = {}
clientsSB = {}
sessions = {}

FL = 0
AL = 1
BL = 2
RL = 3

mydb = cfg.mydb
mycursor = mydb.cursor()
redirect = cfg.redirect

def safesend(socket,data):
	try:
		socket.send((data+"\r\n").encode())
		print(f"S>C: {data}")
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
		
def getfriendcount(email):
	sqlarg = (email, )
	sqlcmd = "SELECT * FROM friendlist WHERE email = %s AND list = 1"
	mycursor.execute(sqlcmd,sqlarg)
	friendlist = mycursor.fetchall() #it breaks if i dont add this
	return mycursor.rowcount
		
def sendlist10(conn,list,sync,usergroup,email,version):
	usercounting = 1
	sqlarg = (email, list)
	sqlcmd = "SELECT * FROM friendlist WHERE email = %s AND list = %s"
	mycursor.execute(sqlcmd,sqlarg)
	friendlist = mycursor.fetchall()
	usercount = mycursor.rowcount
	
	for friend in friendlist:
		if friend[4] == list:
			conn.send(f"LST N={friend[2]} F={friend[3]} C={uuid.uuid4().hex}\r\n".encode()) #more stubs
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
	
	with threading.Lock():
		for friend in friendlist:
			if friend[2] in clients:
				conn.send(f"ILN {sync} {clients[friend[2]]['status']} {friend[2]} {friend[3]}\r\n".encode())
			else:
				conn.send(f"ILN {sync} FLN {friend[2]} {friend[3]}\r\n".encode())
		
def sendtoallfriends(email,data):
	with threading.Lock():
		for x in getallfriends(email):
			if x[2] in clients:
				#clients[x[2]]['conn'].send(data)
				print(f"{email} {data}")
				safesend(clients[x[2]]['conn'],data)

def sendover(conn,sync,email,version,msnver,nickname):
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
		conn.send(f"LSG Other%20Contacts bf9a6841-9d78-4b64-b056-3e80ee0dd47b\r\n".encode())
		print("msnp10 stubby stub stub")
		usergroup = 0
	elif msnver >= 7:
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
	
def sendtoallsession(conn,session,email,data): #leave email blank to send to all including you
	with threading.Lock():
		print(sessions)
		for user in sessions[session]:
			if user != email:
				safesend(clientsSB[user],data)
				print(f"{user} {data}")