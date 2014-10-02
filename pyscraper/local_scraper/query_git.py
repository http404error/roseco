import requests
from requests.auth import HTTPBasicAuth
import json

import sys

import db_control

def extractFromLod(lod, keys):
	# lod is a list of dictionaries
	lot = [] # extracts and returns a list of tuples

	for d in lod:
		# use a list before casting it to a tuple and appending it to lot
		l = []
		for key in keys:
			#begin by trying to extract from the first level list of dicts
			try:
				if key == 'created_at' or key == 'closed_at':
					# we know this is a date
					date = d[key]
					# but it might be None (an open issue)
					if date != None:
						date = date[:date.find('T')]
					l.append(date)
				else:
					l.append( d[key] )
				continue

			except:
				try:
					l.append( d[key[0]][key[1]] )
					continue
				except:
					# if there is an empty list (unlabeled issue) or
					# if there is a None type object
					# append None
					if d[key[0]] == None:
						l.append(None)
					elif len(d[key[0]]) == 0:
						l.append(None)
					else:
						labels = ''
						for nstd_dict in d[key[0]]:
							labels += nstd_dict[key[1]] + ','
						l.append(labels[:-1]) # remove the extra comma on the last one
		
		# cast the list to a tuple to fit the sql multiple row insertion format
		lot.append(tuple(l))

	# returns a list of tuples
	return lot

def splitNameInfo(pkg_repo_info):
	split = pkg_repo_info.find('=')
	name = pkg_repo_info[:split]
	repo_info = pkg_repo_info[split+1:]

	# if there wasn't a git url then pass on the failed message
	if 'noGit' in repo_info:
		return name, repo_info, repo_info

	#otherwise extract the org and repo info we need
	repo_info = repo_info.split(',')
	org = repo_info[0]
	repo = repo_info[1]

	return name, org, repo

def getIssueInfo(src, keys, repo_id):
	lot = []
	for d in src:
		l = []
		for key in keys:
			if type(key) == type(['a', 'list']):
				nstd = d[key[0]]
				if type(nstd) == type(['a', 'list']):
					# nested list of dicts
					if len(nstd) == 0:
						val = None
					else:
						val = ''
						for nstd_d in nstd:
							val += nstd_d[key[1]]
				elif type(nstd) == type({'a':'dict'}):
					# just one nested dict
					val = nstd[key[1]]
				elif nstd == None:
					val = None
				else:
					print "Unknown format", key
					return
			else:
				# first level dict
				val = d[key]
			if type(val) == type(u'str') and val.count(':') == 2 and 'T' in val:
				#This is a date time string, so strip the time
				val = val[:val.find('T')]
			l.append(val)
		l.append(repo_id)
		lot.append(tuple(l))
	
	return lot

def makeIssueQuery(repo_name, page_num = 1):
	q = 'https://api.github.com/repos/'
	q += repo_name + '/issues?state=all&per_page=100&page=' + str(page_num)
	return q

def getRepoInfo(src, keys):
	l = []
	for key in keys:
		if type(key) == type(['a', 'list']):
			nstd = src[key[0]]
			for k in key[1:]:
				nstd = nstd[k]
			val = nstd
		else:
			val = src[key]
		if type(val) == type(u'str') and val.count(':') == 2 and 'T' in val:
			val = val[:val.find('T')]
		l.append(val)

	return tuple(l) 

def makeRepoQuery(repo_name):
	q = 'https://api.github.com/repos/' + repo_name
	return q

if __name__ == '__main__':
	# test query urls
	# url = 'https://api.github.com/repos/turtlebot/turtlebot_simulator/issues'
	# url = 'https://api.github.com/repos/ros/ros_comm/issues?page=1&per_page=100'
	# url = 'https://api.github.com/repos/ros/ros_comm/issues?page=1&per_page=100'

	# query = 'https://api.github.com/repos/turtlebot/turtlebot_simulator/issues'
	# query = 'https://api.github.com/repos/ros/ros_comm'

	# r = requests.get(query, auth = HTTPBasicAuth('twthornt@colby.edu', 'c201b0b14cbf8ec976afa94e3b2cc45f456b3260'))
	# d = json.loads(r.text, )
	# getRepoInfo(d, ['full_name', ['owner', 'type'], 'created_at', 'updated_at', 'pushed_at',
	# 	            'size', 'watchers_count', 'subscribers_count'])
	


	# repo_names = db_control.retrieveTableData(db = 'testdb', table = 'Repos',
	# 	            cols = ['name', 'id'], with_col_name = False, order_by = 'id', desc= False)
	# full_lot = []
	# created = []
	# for repo_name in repo_names:
	# 	print repo_name[0], repo_name[1]
	# 	if 'noGit' in repo_name[0] or repo_name[0] in created:
	# 		continue
	# 	else:
	# 		last_page = False
	# 		page_num = 1
	# 		while last_page == False:
	# 			query = makeIssueQuery(repo_name[0], page_num)
	# 			print query
	# 			r = requests.get(query, auth = HTTPBasicAuth('twthornt@colby.edu', 'c201b0b14cbf8ec976afa94e3b2cc45f456b3260'))
	# 			lod = json.loads(r.text)
	# 			if len(lod) == 0:
	# 				break
	# 			lot = getIssueInfo(lod, keys = [['labels', 'name'],['user', 'login'], 
	# 				['assignee', 'login'],'created_at', 'closed_at'], repo_id = repo_name[1])
	# 			full_lot.extend(lot)
	# 			if len(lod) != 100:
	# 				last_page = True
	# 			else:
	# 				page_num += 1
	# 		created.append(repo_name[0])

	# db_control.makeTableWithFornKey(db='testdb',table='Issues',cols=[["labels", "VARCHAR(50)"],
	# 	["created_by", "VARCHAR(50)"], ["assigned_to", "VARCHAR(50)"],
	# 	["created_at", "VARCHAR(10)"], ["closed_at", "VARCHAR(10)"], ['repo_id','SMALLINT']], 
	# 	data = full_lot,forn_key_name = 'repo_id', forn_key_ref='Repos(id)')









	# repo_names = db_control.retrieveTableData(db = 'testdb', table = 'Packages',
	# 	            cols = ['repos'], with_col_name = False, order_by = 'id')
	# lot = []
	# created = []
	# for repo_name in repo_names:
	# 	if 'noGit' in repo_name[0] or repo_name[0] in created:
	# 		continue
	# 	else:
	# 		try:
	# 			query = makeRepoQuery(repo_name[0])
	# 			r = requests.get(query, auth = HTTPBasicAuth('twthornt@colby.edu', 'c201b0b14cbf8ec976afa94e3b2cc45f456b3260'))
	# 			d = json.loads(r.text)
	# 			t = getRepoInfo(d, ['full_name', ['owner', 'type'], 'created_at', 'updated_at', 
	# 				'pushed_at', 'size', 'forks_count', 'watchers_count', 'subscribers_count'])
	# 			lot.append(t)
	# 			created.append(repo_name[0])
	# 		except:
	# 			print query
	# 			sys.exit()
	
	# print len(created)
	# print lot

	# db_control.makeAutoIncTable(db='testdb',table='Repos',cols=[['name','VARCHAR(50)'],
	# 	['owner_type','VARCHAR(30)'],['created_at','VARCHAR(12)'],['updated_at','VARCHAR(12)'],
	# 	['pushed_at','VARCHAR(12)'],['size','MEDIUMINT'],['forks_count', 'SMALLINT'],
	# 	['watchers_count','SMALLINT'],['subscribers_count','SMALLINT']], data = lot)


	


	# table holds owner/repos strings for each package
	# returns a list of tuples
# 	data = db_control.retrieveTableData(db = 'gitdb', table = 'pkg_repos',
# 		                                cols = 'all', with_col_name = False, 
# 		                                order_by = 'pkg_name')
	
# 	pkg_table_names = [] # pairs package name and github repo
# 	created_table_names = [] # track the tables created for each git repo

# 	s = 0 # counters for successes and failures
# 	f = 0
# 	c = 0
# 	for row in data:
		
# 		name = row[0]
# 		owner_repo = row[1]
# 		print "\n\n", name, owner_repo

# 		c+=1
# 		print c, ":", len(pkg_table_names)

# 		if 'noGit' in owner_repo:
# 			# list this package with the noGit or noGitnoWiki string
# 			# meaning it also lacks a table
# 			print "noGit"
# 			pkg_table_names.append( (name, owner_repo) )
# 			continue

# 		else:
# 			# name of the potential table that holds the github info for this repo
# 			table_name = owner_repo

# 		if table_name in created_table_names:
# 			print "Table already created"
# 			pkg_table_names.append ( (name, table_name) )
# 			continue

# 		# Make the initial git API query with user and repo and request it
# 		query = createGitQueryUrl(owner_repo)
# 		print "Query generated:", query

# 		# for repos with several hundred issues set up a while loop to
# 		# deal with pagination in the api query
# 		lod_len = 100 # keeps track of the returned dictionaries length
# 		# each succesive list of tuples in while loop is appended to this one
# 		full_lot = []

# 		try:
# 			lot = []
# 			while True:
# 				print query[-1], "Page:", query
				
# 				#pass github authentification token as well
# 				r = requests.get(query, auth = HTTPBasicAuth('twthornt@colby.edu', 'c201b0b14cbf8ec976afa94e3b2cc45f456b3260'))

# 				# Creates a list of dictionaries from the json
# 				lod = json.loads(r.text)

# 				# in case the repo has a # of issues divisible by 100
# 				if len(lot) != 0 and len(lod) == 0:
# 					print "Issue # divisible by 100"
# 					break
 
# 				lot = extractFromLod(lod = lod, 
# 				                     keys = ['number', ['labels', 'name'], 
# 			                                ['user', 'login'], ['assignee', 'login'], 
# 			                                'created_at', 'closed_at'])
				
# 				full_lot.extend(lot)
# 				lod_len = len(lod) # update dictionary length variable to reflect this result
# 				print "# of Issues:", lod_len
# 				if lod_len != 100:
# 					# ensure while loop breaks
# 					break
# 				query = nextPageQuery(query)

# 			# Once all pages of issues have been read through and the full list of tuples made
# 			# use table_name from above to name the table
# 			db_control.overwriteTable(db = 'gitdb', table = table_name, 
# 				         cols = [["number", "INTEGER"], ["labels", "VARCHAR(50)"], 
# 				                ["created_by", "VARCHAR(50)"], ["assigned_to", "VARCHAR(50)"],
# 				                ["created_at", "VARCHAR(50)"], ["closed_at", "VARCHAR(50)"]],
# 			             data = full_lot)

# 			# append this table's name to the created list to avoid duplicates
# 			created_table_names.append(table_name)
# 			# pair this package with the table_name
# 			pkg_table_names.append( (name, table_name) )

# 			s += 1
# 			print "Successful table creation", table_name, "number: ", s

# 		except:
# 			f += 1
# 			print "Failed", table_name, "number", f
# 			# failed query of git, no table made for this package
# 			pkg_table_names.append( (name, 'noGitTable') )
# 			# sys.exit()

# print "s:", s
# print "f:", f
# print len(pkg_table_names)

# db_control.overwriteTable(db = 'gitdb', table = 'pkg_table_names', 
# 	                      cols = [["pkg_name", "VARCHAR(50)"], ["table_name", "VARCHAR(50)"]],
#                           data = pkg_table_names)