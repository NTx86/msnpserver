import socket
import mysql.connector
import threading
import random
import config as cfg
import uuid
from util import *
from msnpfunc import *
from msnpsbfunc import *

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
					#sendtoallfriends(email,f"ILN 1 FLN {email} {username}")
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
				if cmd == "PRP":
					cmdPRP(conn,ndata,email)
					continue
			#conn.close()
			#break
			#conn.send(data)  # echo
		conn.close()
	except socket.error as e:
		sendtoallfriends(email,f"ILN 1 FLN {email} {username}")
		if email in clients:
			del clients[email]
		conn.close()
	finally:
		sendtoallfriends(email,f"ILN 1 FLN {email} {username}")
		if email in clients:
			del clients[email]
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
