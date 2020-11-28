import mysql.connector

portnf = 1863
portsb = 53641
redirect = "127.0.0.1:53641"

mydb = mysql.connector.connect(
  host="",
  user="",
  password="",
  database=""
)
mycursor = mydb.cursor()