#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import sys

def conCur(user, passwd, db, host, port):
	# establishes a connection and cursor with a database
	if port != None:
		con = mdb.connect(user=user, passwd=passwd, db=db, host=host, port=port)
	else:
		con = mdb.connect(user=user, passwd=passwd, db=db, host=host)
	cur = con.cursor() # cursor is used to traverse the records from the result set
	return con, cur

# Table Updater
def updateTable(con, cur, table, col_names, col_types, data, fkey_ref = ''):
	if tableExists(cur,table) == False: # If were trying to update a non existant table
		print 'Cannot update a nonexistant table, creating table', table
		makeTableIfNot(con=con,cur=cur,table=table,col_names=col_names,col_types=col_types,data=data,fkey_ref=fkey_ref)
		return

	updateColTypes(con=con,cur=cur,table=table,col_names=col_names,col_types=col_types,fkey_ref=fkey_ref)
	# Format insert row cmd with col_names
	cmd = 'INSERT INTO ' + table + ' ('
	cmd2 = ''
	cmd3 = ' ON DUPLICATE KEY UPDATE '
	for col_name in col_names:
		cmd += col_name + ', '
		cmd2 += '%s, ' # Use string formatting regardless of type
		if col_name != col_names[0]:
			cmd3 += col_name + ' = VALUES(' + col_name + '), '
	cmd = cmd[:-2] + ') VALUES(' + cmd2[:-2] + ')' + cmd3[:-2] # cut off exta comma & space
	cur.executemany(cmd, data)
	con.commit()

# Update table helpers:
def updateColTypes(con, cur, table, col_names, col_types, fkey_ref):
	table = '`'+table +'`'
	cmd = 'SHOW COLUMNS FROM '+table
	result = exFetch(cur,cmd)
	
	for idx,col_type in enumerate(col_types):
		# Update types
		if col_type.lower() != result[idx][1]:
			print "  Modifying Column Types for", table
			cmd = 'ALTER TABLE '+table+' MODIFY '+col_names[idx]+' '+col_type
			print "    " + cmd
			cur.execute(cmd)

		# Update fkeys, fkey always last and colname has '_id' in it
		if idx+1 == len(col_names) and '_id' in col_names[idx]:
			if fkey_ref != '' and result[idx][3] == '':
				cmd = 'ALTER TABLE '+table+' ADD FOREIGN KEY ('+col_names[idx]+') REFERENCES '+fkey_ref
				print cmd
				cur.execute(cmd)
	con.commit()

def tableExists(cur, table):
	cmd = 'SHOW TABLES'
	table = table.replace('`','')
	r = exFetch(cur,cmd)
	for t in r:
		if t[0] == table: # Table names can have backticks
			return True
	return False

def makeTableIfNot(con,cur,table,col_names,col_types,data,fkey_ref):
	table = '`'+table +'`'
	cmd = 'CREATE TABLE ' + table + ' ('
	for idx,col_name in enumerate(col_names):
		cmd += col_name + ' ' + col_types[idx] + ', '
	cmd += 'PRIMARY KEY (id)'
	if fkey_ref != '': 
		cmd +=', FOREIGN KEY ('+col_names[-1]+') REFERENCES '+fkey_ref
	cmd += ')'
	cur.execute(cmd)

	cmd = 'INSERT INTO ' + table + ' ('
	cmd2 = ''
	for col_name in col_names:
		cmd += col_name + ', '
		cmd2 += '%s, ' # Use string formatting regardless of type
	cmd = cmd[:-2] + ') VALUES(' + cmd2[:-2] + ')'
	cur.executemany(cmd, data)
	#con.commit()

# Table creators
def makeMapTable(con, cur, table, key_names, key_refs, data):
	table = '`' + table + '`'
	if tableExists(cur, table): cur.execute('DROP TABLE ' + table)
	
	cmd = 'CREATE TABLE ' + table + '('
	next_cmd = ''
	for i in range(len(key_names)):
		cmd += key_names[i] + ' SMALLINT, '
		next_cmd += 'FOREIGN KEY ('+key_names[i]+') REFERENCES '+key_refs[i]+ ', '
	cmd = cmd + next_cmd[:-2] + ')'
	cur.execute(cmd)

	cmd = 'INSERT INTO ' + table + '('
	next_cmd = ''
	for key_name in key_names:
		cmd += key_name + ', '
		next_cmd += '%s, '
	cmd = cmd[:-2] + ') VALUES(' + next_cmd[:-2] + ')'
	
	cur.executemany(cmd, data)
	con.commit()

def makeScoreTable(con, cur, table, col_names, col_types, fkey_ref, data):
	# Score tables contain a foreign key and a score, so they are technically linked tables
	# but require a separate function to deal with: foreign keys in zeroth index, no primaray keys,
	# and only one foreign key (can't be mapping table)
	table = '`' + table + '`'
	if tableExists(cur, table): cur.execute('DROP TABLE ' + table)

	cmd = 'CREATE TABLE ' + table + ' ('
	for i in range(len(col_names)):
		cmd += col_names[i] + ' ' + col_types[i] + ', '
	cmd += 'FOREIGN KEY ('+col_names[0]+') REFERENCES '+fkey_ref+')'
	cur.execute(cmd)

	# Format insert row cmd with col_names
	cmd = 'INSERT INTO ' + table + '('
	next_cmd = ''
	for col_name in col_names:
		cmd += col_name + ', '
		next_cmd += '%s, ' # Use string formatting regardless of type
	cmd = cmd[:-2] + ') VALUES(' + next_cmd[:-2] + ')' # cut off exta comma & space
	cur.executemany(cmd, data)
	con.commit()

# Table retrievers
# Only need a cur (not con as well) because cur executres queries on its own, con just commits

def getTable(cur, table, cols, row_max=None):
	table = '`' + table + '`'
	cmd = 'SELECT '
	for col in cols:
		cmd += col + ', '
	cmd = cmd[:-2] + ' FROM %s ' % table
	if row_max != None: cmd += 'WHERE id <= ' + str(row_max) + ' '
	cmd += 'ORDER BY id ASC'
	result = list(exFetch(cur,cmd))
	return result

def getMatch(cur, table, cols, match_col, val, num=False):
	table = '`' + table + '`'
	cmd = 'SELECT '
	for col in cols:
		cmd += col + ', '
	cmd = cmd[:-2] + ' FROM '+table+' WHERE '+match_col+' = '+str(val)
	result = exFetch(cur,cmd)

	if num == True:
		return len(result)
	else:
		return result

def getDepOrders(cur, dep_id):
	# Used for impact scoring
	dep_orders = []
	cmd = 'SELECT DISTINCT pkg_id FROM PkgDeps WHERE dep_id = ' + str(dep_id)
	result = exFetch(cur, cmd)

	def addOrder(dep_orders, result):
		this_dep_order = set()
		for dep_id in result:
			if not any(dep_id in dep_order for dep_order in dep_orders):
				this_dep_order.add(dep_id[0])
		dep_orders.append(this_dep_order)
		return dep_orders

	# Seed with direct dependencies
	dep_orders = addOrder(dep_orders, result)

	while_count = 0
	while while_count < 10:
		if while_count == 0:
			cmd = cmd.replace('=','!=') + ' AND dep_id IN (' + cmd + ')'
		else:
			cmd = cmd.replace(' AND dep_id IN ', ' AND dep_id NOT IN ') + ' AND dep_id IN (' + cmd + ')'
		result = exFetch(cur, cmd)
		if len(result) == 0:
			break
		dep_orders = addOrder(dep_orders, result)
		while_count += 1

	# Only return the number of dependency for each order
	dep_order_nums = []
	if len(dep_orders) == 0:
		dep_order_nums.append(0)
	else:
		for dep_order in dep_orders:
			dep_order_nums.append(len(dep_order))
	return dep_order_nums

# Helper retriever
def exFetch(cur,cmd):
	cur.execute(cmd)
	return cur.fetchall()


# Useless?

# def makeTable(con, cur, table, col_names, col_types, data):
# 	table = '`' + table + '`'
# 	cmd = 'DROP TABLE IF EXISTS ' + table
# 	cur.execute(cmd)
	
# 	cmd = 'CREATE TABLE ' + table + ' ('
# 	# Set up the col names and col types
# 	for i in range(len(col_names)):
# 		cmd += col_names[i] + ' ' + col_types[i] + ', '
# 	cmd += "PRIMARY KEY (id))"
# 	cur.execute(cmd)

# 	# Format insert row cmd with col_names
# 	cmd = 'INSERT INTO ' + table + '('
# 	next_cmd = ''
# 	for col_name in col_names:
# 		cmd += col_name + ', '
# 		next_cmd += '%s, ' # Use string formatting regardless of type
# 	cmd = cmd[:-2] + ') VALUES(' + next_cmd[:-2] + ')' # cut off exta comma & space
	
# 	cur.executemany(cmd, data)
# 	con.commit()

# def makeLinkedTable(con, cur, table, col_names, col_types, fkey_ref, data):
# 	# Foreign key name and type are the last elements in col_names and col_types
# 	table = '`' + table + '`'
# 	cmd = 'DROP TABLE IF EXISTS ' + table
# 	cur.execute(cmd)

# 	# cmd = 'CREATE TABLE ' + table + ' (id SMALLINT NOT NULL AUTO_INCREMENT, '
# 	cmd = 'CREATE TABLE ' + table + ' ('
# 	for i in range(len(col_names)):
# 		cmd += col_names[i] + ' ' + col_types[i] + ', '
# 	cmd += 'PRIMARY KEY (id), FOREIGN KEY ('+col_names[-1]+') REFERENCES '+fkey_ref+')'
# 	cur.execute(cmd)

# 	# Format insert row cmd with col_names
# 	cmd = 'INSERT INTO ' + table + '('
# 	next_cmd = ''
# 	for col_name in col_names:
# 		cmd += col_name + ', '
# 		next_cmd += '%s, ' # Use string formatting regardless of type
# 	cmd = cmd[:-2] + ') VALUES(' + next_cmd[:-2] + ')' # cut off exta comma & space
# 	cur.executemany(cmd, data)
# 	con.commit()

# def dropAllTables(con, cur):
# 	cmd = 'DROP TABLES `Issues`, `PkgDeps`, `PkgAuthors`, `PkgMntnrs`, `PkgImpact`, `PkgHealth`, `PplImpact`'
# 	cur.execute(cmd)
# 	cmd = 'DROP TABLES `People`, `Packages`'
# 	cur.execute(cmd)
# 	cmd = 'DROP TABLES `Repos`'
# 	cur.execute(cmd)
# 	con.commit()

# def getUniqueDepIds(cur):
# 	cmd = 'SELECT DISTINCT dep_id from PkgDeps;'
# 	cur.execute(cmd)
# 	result = cur.fetchall()
# 	return result

# def getDepOrders(cur, dep_id):
# 	dep_orders = []
# 	# Begin by getting the number of first order (direct) dependencies
# 	cmd = 'SELECT DISTINCT pkg_id FROM PkgDeps WHERE dep_id = ' + str(dep_id)
# 	cur.execute(cmd)
# 	result = cur.fetchall()
	
# 	# Set up a while loop to get the successive orders of dependencies inclusively
# 	old_order = 0
# 	new_order = len(result)
# 	while new_order != old_order:
# 		dep_orders.append(new_order - old_order)
# 		if len(dep_orders) == 10:
# 			print dep_id, dep_orders
# 			sys.exit()
# 		old_order = new_order
		
# 		cmd += ' OR dep_id IN (' + cmd + ')'
# 		cur.execute(cmd)
# 		result = cur.fetchall()
		
# 		new_order = len(result)

# 	if len(dep_orders) == 0:
# 		dep_orders.append(0)

# 	return dep_orders


if __name__ == '__main__':
	# con, cur = concur(user='smartroswiki', passwd='p0tyYjIr', db='smartroswiki', host='engr-db.engr.oregonstate.edu', port=3307)
	con, cur = conCur(user='dbuser',passwd='dbpass',db='test2',host='localhost',port=None)