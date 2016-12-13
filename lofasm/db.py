#module for connecting to the LoFASM Control Computer Database


import MySQLdb as mdb
from .config import dbhost, dbname, dbuser, dbpass

def dbconnect():
	try:
		db = mdb.connect(dbhost, dbuser, dbpass, dbname)
	except:
		raise RuntimeError("cold not connect to database")

	return db.cursor()