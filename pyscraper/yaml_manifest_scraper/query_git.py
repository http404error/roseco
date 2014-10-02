import requests
from requests.auth import HTTPBasicAuth
import json
from unidecode import unidecode
import sys

token = 'c201b0b14cbf8ec976afa94e3b2cc45f456b3260'
email = 'twthornt@colby.edu'

def makeRepoQuery(repo_name):
	repo_query = 'https://api.github.com/repos/' + repo_name
	return repo_query

def makeIssuesQuery(repo_name, page_num):
	issue_query = 'https://api.github.com/repos/' + repo_name
	issue_query += '/issues?state=all&per_page=100&page=' + str(page_num)
	return issue_query

def executeQuery(query, email = email, token = token):
	req = requests.get(query, auth=HTTPBasicAuth(email, token))
	result = json.loads(req.text)
	return result

def didQueryFail(a_dict, keys):
	# If the query failed
	if len(a_dict) == 2:
		if 'message' in a_dict:
			if a_dict['message'] == 'Not Found' or \
		 	   a_dict['message'] == 'Issues are disabled for this repo':
				return True
	return False

def makeNoneList(keys):
	return [None for i in range(len(keys))]

def getRepoVals(repo_dict, keys):
	if didQueryFail(repo_dict, keys):
		return makeNoneList(keys)

	l = []
	for key in keys:
		if type(key) == type(['list']):
			# a nested value
			val = repo_dict[key[0]][key[1]]
		else:
			val = repo_dict[key]
		
		# convert unicode to ascii equivalent
		if type(val) == type(u'unicode'): val = unidecode(val)
		# cut off time in timedate strings
		if type(val) == type('str') and val.count(':') == 2: val = val[:val.find('T')]

		l.append(val)

	return l

def getIssuesVals(issues_list, keys):
	if didQueryFail(issues_list, keys):
		return makeNoneList(keys)

	# Return a list of lists (rather than a list of tuples) because we will need to add a
	# linking forieng key from Repos table to each issue
	lol = []
	for issue_dict in issues_list:
		l = []
		for key in keys:
			if type(key) == type(['list']):
				nstd = issue_dict[key[0]]
				if type(nstd) == type(['list']):
					if len(nstd) == 0: val = None
					else:
						val = ''
						for nstd_d in nstd:
							val += nstd_d[key[1]]
				elif type(nstd) == type({'a':'dict'}):
					val = nstd[key[1]]
				elif nstd == None:
					val = None
				else:
					print "Unknown format for ", key
					sys.exit()
			else:
				val = issue_dict[key]

			# Unidecode conversion and date from datetime extraction
			if type(val) == type(u'unicode'): val = unidecode(val)
			if type(val) == type('str') and val.count(':') == 2: val = val[:val.find('T')]

			l.append(val)
		lol.append(l)
	return lol

def getRepoInfo(repo_name, keys):
	print '  ', repo_name
	repo_query = makeRepoQuery(repo_name)
	repo_dict = executeQuery(repo_query)
	repo_info = getRepoVals(repo_dict, keys)
	return repo_info

def getIssuesInfo(repo_name, keys):
	print '  ', repo_name
	repo_issues_info = []
	this_issues_info = []
	page_num = 1
	last_page = False # Stopping condition 1: if we run out of issues
	none_list = makeNoneList(keys) # Stopping condition 2: if the repo_name is invalid
	while last_page == False and this_issues_info != none_list:
		issue_query = makeIssuesQuery(repo_name, page_num)
		issues_list = executeQuery(issue_query)
		if len(issues_list) == 0:
			last_page = True
			# Just break before going through value retrieval if there are no issues
			break
		this_issues_info = getIssuesVals(issues_list, keys)
		repo_issues_info.extend(this_issues_info)
		page_num += 1

	return repo_issues_info

def getRemaininder():
	result = executeQuery('https://api.github.com/rate_limit')
	print result['rate']['remaining']

if __name__ == '__main__':
	# issues_info_keys = [['user', 'login'], ['assignee', 'login'],'created_at', 'closed_at', 
	#                     ['labels', 'name']]
	# print getIssuesInfo('cram-code/cram_3rdparty', issues_info_keys)
	getRemaininder()