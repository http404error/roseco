#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import sys
import package as pk
import scorer as sc

# SQL command lines

# To open mysql in terminal
# mysql -u root -p
# Robots!

# USE rosdb;
# SELECT * FROM `<table name>`;

# To create new database
# CREATE DATABASE <dbname>;

# To find a row by name
# SELECT * FROM <table name> WHERE name='name';

# To get the name of every table in a datbase
# SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA='testdb';



def concur(db):
	# establishes a connection and cursor with a database
	con = mdb.connect(host = 'localhost', user = 'dbuser', 
		              passwd = 'dbpass', db = db);

	cur = con.cursor() # cursor is used to traverse the records from the result set
	return con, cur

def overwriteTable(db, table, cols, data):
	# cols is a list of lists, each nested list contains the name and type
	# data is a list of tuples, each tuple is a row

	#add back ticks before and after table name to prevent errors with - and / chars
	table = '`' + table + '`'
	
	#establish a connection and cursor with the git data base
	con, cur = concur(db)

	# drop the table if it already exists
	cmd = 'DROP TABLE IF EXISTS ' + table
	cur.execute(cmd)

	# create the table again
	cmd = 'CREATE TABLE ' + table + '('
	
	# set up the col names and col types
	for col in cols:
		cmd += col[0] + ' ' + col[1] + ', '
	# remove the extra space and comma at the end from the for loop above
	cmd = cmd[:-2]
	cmd += ')'

	cur.execute(cmd)

	# create the prefix to the insert row cmd, which involves only column titles
	cmd = "INSERT INTO " + table + "("
	for col in cols:
		cmd += col[0] + ", "
	cmd = cmd[:-2]
	cmd += ") VALUES("
	
	for col in cols:
		cmd += '%s, '
	cmd = cmd[:-2] + ')'
	
	# now that our cmd is made, executemany with the data (list of tuples)
	cur.executemany(cmd, data)

	# save the changes to this table
	con.commit()

def retrieveTableData(db, table, cols, with_col_name, order_by, desc = True):
	table = '`' + table + '`'
	con, cur = concur(db)
	if cols == 'all':
		cmd = 'SELECT * FROM %s ' % table
	else:
		cmd = "SELECT "
		for i in range(len(cols)):
			if i == (len(cols) - 1):
				cmd += cols[i]
			else:
				cmd += cols[i] + ', '
		cmd += ' FROM %s ' % table
	
	cmd += 'ORDER BY %s ' % order_by
	if desc == True:
		 cmd += 'DESC'
	else:
		cmd += 'ASC'
	cur.execute(cmd)

	if cols == 'all':
		cols = [i[0] for i in cur.description]	
	result = list(cur.fetchall())
	if with_col_name == True:
		result.insert(0, tuple(cols)) #make it a tuple to maintain the list of tuples format
	
	return result

def generateLotData(data_from, data_values):
	# generated data from either packages or people as a list of tuples, 
	# each element of the tuple is some value derived from the object
	# lot can be passed to overwriteTable in the data parameter
	lot = []
	if type(data_from) == type({'a':'dict'}):
		for package in data_from.values():
			l = []
			for d_v in data_values:
				l.append(eval(d_v))
			# make the list into a tuple
			lot.append(tuple(l))
	elif type(data_from) == type(set(['a','set'])):
		for people in data_from:
			l = []
			for d_v in data_values:
				l.append(eval(d_v))
			lot.append(tuple(l))
	return lot

def makeTableWithPriKey(db, table, cols, data):
	table = '`' + table + '`'
	con, cur = concur(db)
	
	cmd = 'DROP TABLE IF EXISTS ' + table
	cur.execute(cmd)
	cmd = 'CREATE TABLE ' + table + ' (id SMALLINT NOT NULL AUTO_INCREMENT, '
	
	# set up the col names and col types
	for col in cols:
		cmd += col[0] + ' ' + col[1] + ', '
	cmd += "PRIMARY KEY (id))"
	
	cur.execute(cmd)

	# create the prefix to the insert row cmd, which involves only column titles
	cmd = "INSERT INTO " + table + "("
	for col in cols:
		cmd += col[0] + ", "
	cmd = cmd[:-2]
	cmd += ") VALUES("
	
	for col in cols:
		cmd += '%s, '
	cmd = cmd[:-2] + ')'
	
	cur.executemany(cmd, data)
	con.commit()

def makeTableWithPriFornKey(db, table, cols, data, forn_key_name, forn_key_ref):
	table = '`' + table + '`'
	con, cur = concur(db)

	cmd = 'DROP TABLE IF EXISTS ' + table
	cur.execute(cmd)
	cmd = 'CREATE TABLE ' + table + ' (id SMALLINT NOT NULL AUTO_INCREMENT, '
	
	# set up the col names and col types
	for col in cols:
		if col[0] == forn_key_name:
			continue
		cmd += col[0] + ' ' + col[1] + ', '
	cmd += forn_key_name + ' SMALLINT, '
	cmd += "PRIMARY KEY (id), FOREIGN KEY ("+forn_key_name+") REFERENCES "+forn_key_ref+")"
	cur.execute(cmd)

	# create the prefix to the insert row cmd, which involves only column titles
	cmd = "INSERT INTO " + table + "("
	for col in cols:
		cmd += col[0] + ", "
	cmd = cmd[:-2]
	cmd += ") VALUES("
	
	for col in cols:
		cmd += '%s, '
	cmd = cmd[:-2] + ')'
	
	cur.executemany(cmd, data)
	con.commit()

def makeMapTable(db, table, forn_keys, key_pairs):
	table = '`' + table + '`'
	con, cur = concur(db)
	cmd = 'DROP TABLE IF EXISTS ' + table
	cur.execute(cmd)
	
	cmd = 'CREATE TABLE ' + table + '('
	cmd_next = ''
	for k in forn_keys:
		cmd += k[0] + ' SMALLINT, '
		cmd_next += 'FOREIGN KEY ('+k[0]+') REFERENCES '+k[1] + ', '
	cmd = cmd + cmd_next[:-2] + ')'
	cur.execute(cmd)

	cmd = 'INSERT INTO ' + table + '('
	cmd_next = ''
	for k in forn_keys:
		cmd += k[0] + ', '
		cmd_next += '%s, '
	cmd = cmd[:-2] + ') Values(' + cmd_next[:-2] + ')'
	cur.executemany(cmd, key_pairs)
	con.commit()

def updateCol(db, table, col, data):
	table = '`' + table + '`'
	con, cur = concur(db)
	for row in data:
		cmd = 'UPDATE '+table+' SET '+col+'='+"'"+str(row[0])+"'"+' WHERE repo ='+"'"+row[1]+"'"
		cur.execute(cmd)
	con.commit()

if __name__ == '__main__':
	packages = pk.makePackageList('/opt/ros/hydro/share')
	packages = sc.scorePackages(packages)
	people = sc.scorePeople(packages)

	
	# pkg_lot = retrieveTableData(db='testdb', table='Packages', cols=['id','name'], 
	# 	with_col_name=False, order_by='id', desc = False)
	# ppl_lot = retrieveTableData(db='testdb',table='People',cols=['id','name'],
	# 	with_col_name=False,order_by='id',desc=False)
	# pkgm_lot = []
	# pkga_lot = []
	# for pkg_t in pkg_lot:
	# 	for ppl_t in ppl_lot:
	# 		if packages[pkg_t[1]].maintainers.find(ppl_t[1]) != None:
	# 			pkgm_lot.append(tuple([pkg_t[0],ppl_t[0]]))
	# 		if packages[pkg_t[1]].authors.find(ppl_t[1]) != None:
	# 			pkga_lot.append(tuple([pkg_t[0],ppl_t[0]]))

	# makeMapTable(db='testdb',table='PkgMntnrs', 
	# 	forn_keys=[['pkg_id','Packages(id)'],['ppl_id','People(id)']], key_pairs=pkgm_lot)
	# makeMapTable(db='testdb',table='PkgAuthors', 
	# 	forn_keys=[['pkg_id','Packages(id)'],['ppl_id','People(id)']], key_pairs=pkga_lot)


	# lot = generateLotData(people, ['people.name', 'people.impact','people.pkgs_maintaining',
	# 	'people.pkgs_authored', "', '.join(list(people.emails))"])

	# makeTableWithPriKey(db = 'testdb', table = 'People', cols = [["name", "VARCHAR(60)"], 
	#  	["impact", "FLOAT"],["pkgs_maintaining", "TINYINT"],["pkgs_authored", "TINYINT"],
 #        ["emial", "VARCHAR(50)"]], data = lot)
	



	# data = retrieveTableData(db = 'testdb', table = 'Repos', cols = ['id','name'], 
	#  	                     with_col_name = False, order_by = 'id', desc = False)
	
	# updateCol(db = 'testdb', table = 'Packages', col = 'repo_id', data = data)

	# data = retrieveTableData(db = 'gitdb', table = 'pkg_repos', cols = 'all', 
	# 	                     with_col_name = False, order_by = 'pkg_name', desc = False)
	# updateCol(db = 'testdb', table = 'Packages', col = 'repo', data = data)




	# lot = generateLotData(packages, ['package.name', 'package.impact', 'package.health',
	# 	"(str(package.run_dep_orders_list).strip('[]'))",
	# 	"(str(package.build_dep_orders_list).strip('[]'))", 'None'])

	# makeTableWithFornKey(db = 'testdb', table = 'Packages', cols = [["name", "VARCHAR(50)"], 
	# 	["impact", "FLOAT"],["health", "FLOAT"],["run_dep_orders", "VARCHAR(20)"],
 #        ["build_dep_orders", "VARCHAR(20)"], ['repo', 'VARCHAR(50)']],
 #        data = lot, forn_key_name = 'repo_id', forn_key_ref = 'Repos(id)')




	# lot = generateLotData(packages, ['package.name', 'package.impact', 'package.health',
	# 	"(str(package.run_dep_orders_list).strip('[]'))",
	# 	"(str(package.build_dep_orders_list).strip('[]'))"])

	# makeTableWithFornKey(db = 'testdb', table = 'Packages', cols = [["name", "VARCHAR(50)"], 
	# 	["impact", "FLOAT"],["health", "FLOAT"],["run_dep_orders", "VARCHAR(20)"],
 #        ["build_dep_orders", "VARCHAR(20)"]],
 #        data = lot, forn_key_name = 'repo_id', forn_key_ref = 'Repos(id)')