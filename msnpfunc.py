from util import *
import random

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
			with threading.Lock():
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
			with threading.Lock():
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
	if msnver < 10:
		conn.send(f"SYN {sync} {version}\r\n".encode())
	else:
		conn.send(f"SYN {sync} 2000-01-01T00:00:00.0-00:00 2000-01-01T00:00:00.0-00:00 {getfriendcount(email)} 1\r\n".encode())
		print(f"SYN {sync} 2000-01-01T00:00:00.0-00:00 2000-01-01T00:00:00.0-00:00 {getfriendcount(email)} 1\r\n".encode())
	#if msnver != version:
	sendover(conn,sync,email,version,msnver,nickname)
	
def cmdCHG(conn,data,status,msnver,email,username):
	cmdarg = data.split(' ')
	sync = cmdarg[1]
	status = cmdarg[2]
	print("status is "+status)
	conn.send((data+"\r\n").encode())
	with threading.Lock():
		clients[email]['status'] = status
	sendtoallfriends(email,f"ILN {sync} {status} {email} {username}")
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
		sendtoallfriends(email,f"REA {sync} 19 {useremail} {usernamechg}")
	else:
		with threading.Lock():
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
	with threading.Lock():
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
	
def cmdPRP(conn,ndata,email):
	cmdarg = ndata.split(' ')
	sync = cmdarg[1]
	type = cmdarg[2]
	if type == "MFN":
		usernamechg = cmdarg[3]
		changenickname(usernamechg,email)
		conn.send(f"PRP MFN {usernamechg}\r\n".encode())
		print(f"response: PRP MFN {usernamechg}")
		incrementversion(email)
		return usernamechg