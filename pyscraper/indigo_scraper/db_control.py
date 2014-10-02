#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import db_extract as dbe
import sys

def conCur(user='dbuser',passwd='dbpass',db='test3',host='localhost',port=None):
	# establishes a connection and cursor with a database
	if port != None:
		con = mdb.connect(user=user, passwd=passwd, db=db, host=host, port=port)
	else:
		con = mdb.connect(user=user, passwd=passwd, db=db, host=host)
	cur = con.cursor() # cursor is used to traverse the records from the result set
	return con, cur

def tableExists(cur, name):
	cmd = """SHOW TABLES """
	all_tables = dbe.exFetch(cur, cmd)

	for t in all_tables:
		if t[0] == name: # Name at zeroth index
			return True
	return False

def setFKChecks(cur, set_to):
	cmd = """SET FOREIGN_KEY_CHECKS = {0}""".format(set_to)
	cur.execute(cmd)

def truncateTable(cur, name):
	setFKChecks(cur, 0)
	cmd = """TRUNCATE {0}""".format(name)
	cur.execute(cmd)
	setFKChecks(cur, 1)

def insertCmd(name, col_names):
	cmd = """INSERT INTO {0} (""".format(name)
	cmd2 = ""
	for idx,name in enumerate(col_names):
		cmd += name + ", "
		cmd2 += "%s, "
	return cmd[:-2] + ") VALUES(" + cmd2[:-2] + ")"

def createCmd(name, col_names, col_types, pk=None, fk=None, fk_ref=None):
	cmd = """CREATE TABLE {0} (""".format(name)

	for idx,col_name in enumerate(col_names):
		cmd += "{0} {1}, ".format(col_name, col_types[idx])
	
	if pk != None: 
		cmd += "PRIMARY KEY ({0}), ".format(pk)
	
	if fk != None and fk_ref != None:
		if type(fk) == type(['list']):
			for idx,fk_name in enumerate(fk):
				cmd += "FOREIGN KEY ({0}) REFERENCES {1}, ".format(fk_name, fk_ref[idx])
		else:
			cmd += "FOREIGN KEY ({0}) REFERENCES {1}, ".format(fk, fk_ref)
	
	return cmd[:-2] + ")"

def updateCols(con, cur, name, col_names, col_types, fk_ref):
	cmd = """SHOW COLUMNS FROM """ + name
	cols_info = dbe.exFetch(cur,cmd)
	
	for idx,info in enumerate(cols_info):
		# Name of type discrepancy
		if info[0] != col_names[idx] or info[1] != col_types[idx].lower():
			cmd = """ALTER TABLE {0} CHANGE {1} {2} {3}""".format(
				     name, info[0], col_names[idx], col_types[idx])
			print "  Updating {0} {1} --> {2} {3}".format(
				     info[0], info[1], col_names[idx], col_types[idx])
			cur.execute(cmd)
		# Foreign key discrepancy
		if idx == len(col_names)-1 and '_id' in col_names[idx] \
		and fk_ref != None and info[3] == '':
			cmd = """ALTER TABLE {0} ADD FOREIGN KEY ({1}) REFERENCES {2}""".format(
				     name, col_names[-1], fk_ref)
			print "  Updating Foreign Key {0} Ref {1}".format(col_names[-1], fk_ref)
			cur.execute(cmd)
	
	con.commit()

def upTruncTable(con, cur, name, col_names, col_types, data, 
	            pk = None, fk = None, fk_ref = None):
	
	if tableExists(cur, name) is False:
		print "  {0} does not exist, creating table...".format(name)
		cmd = createCmd(name, col_names, col_types, pk, fk, fk_ref)
		cur.execute(cmd)
	else:
		truncateTable(cur, name)
	
	updateCols(con, cur, name, col_names, col_types, fk_ref)
	
	cmd = insertCmd(name, col_names)
	cur.executemany(cmd, data)

	con.commit()

if __name__ == '__main__':
	# con, cur = concur(user='smartroswiki', passwd='p0tyYjIr', db='smartroswiki', host='engr-db.engr.oregonstate.edu', port=3307)
	con, cur = conCur(user='dbuser',passwd='dbpass',db='test3',host='localhost',port=None)
	# print updateColTypes(con,cur,'People',['id','name','emails'],['SMALLINT(6)','VARCHAR(100)','VARCHAR(50)'],None)
	print insertCmd('Test',['id','name','emails'])
	print createCmd('Test',['id','name','emails'], ['SMALLINT(6)','VARCHAR(100)','VARCHAR(50)'],'id','ppl_id', 'People(id)')