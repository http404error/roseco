import repo

import requests
from requests.auth import HTTPBasicAuth

import json
from base64 import b64decode
import xml.etree.ElementTree as ET
from unidecode import unidecode
from yaml import load

import os
import sys
from datetime import datetime

# Global variables

# Github authentification
token = 'f396cd518f376b497f8820c2e1bcd00701a12e13'
email = 'twthornt@colby.edu'

# Manifest saving directory
dir_path = os.path.dirname(os.path.abspath(__file__)) + '/manifests'

# To avoid traversing too deep in a github repository and finding bogus manifests
max_depth = 5
this_depth = [0] # mutable to keep track of current recursiv depth

def makeContentsQuery(repo_url):
	repo_owner = repo_url.replace('https://github.com/','').replace('.git','')
	query = 'https://api.github.com/repos/' + repo_owner + '/contents'
	return query

def executeQuery(query):
	try:
		req = requests.get(query, auth=HTTPBasicAuth(email, token), verify = False)
		result = json.loads(req.text)
	except:
		print "Failed query", query
		return
	
	if 'message' in result: # Message key only in result if 'Not Found'
		print 'Failed Query:', query
		return
	
	return result

def releaseSearch(repo_url):
	query = makeContentsQuery(repo_url)
	contents = executeQuery(query)
	for item in contents:
		if item['type'] == 'file' and item['name'] == 'tracks.yaml':
			result = executeQuery( query + '/tracks.yaml' )
			tracks = load(b64decode(result['content']))
			try:
				try:
					source_repo = tracks['tracks']['hydro']['vcs_uri'].replace('git@github.com:','').replace('git:','')
					return source_repo
				except:
					source_repo = tracks['tracks']['indigo']['vcs_uri'].replace('git@github.com:','').replace('git:','')
					return source_repo
			except:
				return None

# Recursive breath-first search traversion of directories
def getManifestsBFS(start_query):
	manifests = []
	
	next_queries = [start_query]
	while this_depth[0] < max_depth:
		queries = next_queries
		next_queries = []
		this_depth[0] += 1
		
		for q in queries:
			content = executeQuery(q)
			if content == None: 
				continue
			
			for item in content:
				
				if item['type'] == 'file' and item['name'] == 'package.xml':
					result = executeQuery( q + '/' + item['name'] )
					if result == None: continue
					manifests.append(ET.fromstring(b64decode(result['content'])))
				
				elif item['type'] == 'dir':
					next_queries.append(q + '/' + item['name'])

	this_depth[0] = 0 # reseet the depth count
	return manifests

# Recursively traverse directories of repositories for manifests
def getManifestsDFS(query):
	contents = executeQuery(query)
	manifests = []
	
	# If contents query failed return empty list rather than None
	# in order to prevent any looping by the for loop that uses the result
	if contents == None: return manifests

	for item in contents:
		if item['type'] == 'file' and item['name'] == 'package.xml' or item['name'] == 'manifest.xml':
			result = executeQuery( query + '/' + item['name'] )
			
			# Query failed
			if result == None: continue
			
			manifest = ET.fromstring(b64decode(result['content']))
			manifests.append(manifest)

		elif item['type'] == 'dir':
			# Eventually make this just grab 'self' from links
			dir_query = query + '/' + item['name']
			manifests.extend( getManifests(dir_query) ) # Empty list won't change list with extend
	
	return manifests


def decodeUniText(manifest):
	# Author and maintainers are the ones with unicode names
	# Unnessary to traverse entire contents, instead print
	# a failure in saveManifests and deal with it then
	ptypes = ['maintainer', 'author']
	for ptype in ptypes:
		result = manifest.find(ptype)
		if result != None:
			if type(result.text) == type(u'uni'):
				decoded = unidecode(result.text)
				manifest.find(ptype).text = decoded

	return manifest

def clearManifests():
	file_names = os.listdir(dir_path)
	for f in file_names:
		os.remove(dir_path+'/'+f)

def saveManifests(Repos_dict, wipe = False):
	# Typically around 35 minutes, but is 5000+ queries, so time it right
	# The count resets around 44 minutes into each hour
	
	if wipe: 
		clearManifests()
	
	file_names = os.listdir(dir_path) # should be an empty list
	
	for key,repo in Repos_dict.items():

		saved = False

		for repo_url in repo.urls:
			query = makeContentsQuery(repo_url)
			manifests = getManifestsBFS(query)

			for manifest in manifests:
				name = manifest.find('name').text
				# File name format: repo_name-pkg_name.xml
				file_name = key + '-' + name + '.xml'
				if file_name in file_names: continue # Don't save duplicates
				file_names.append(file_name)
				
				manifest = decodeUniText(manifest)
				
				save_path = os.path.join(dir_path, file_name)
				with open(save_path, 'w') as f:
					try:
						f.write(ET.tostring(manifest))
						saved = True
						print "Saved:", file_name
					except:
						print "\nFailed save:", file_name, "\nfrom repo:", query

		if saved == False:
			print "No manifests saved", key
			for repo_url in repo.urls:
				if 'release' in repo_url: 
					source_url = releaseSearch(repo_url)
					if source_url == None: 
						print " failed release search", repo_url
						break
					
					query = makeContentsQuery(source_url)
					manifests = getManifestsBFS(query)
					for manifest in manifests:
						name = manifest.find('name').text
						file_name = key + '-' + name + '.xml'
						if file_name in file_names: continue
						file_names.append(file_name)
						manifest = decodeUniText(manifest)
						save_path = os.path.join(dir_path, file_name)
						with open(save_path, 'w') as f:
							try:
								f.write(ET.tostring(manifest))
								print "  saved with release tracks:", file_name
							except:
								print "  failed save with release tracks:", file_name, "\nfrom repo:", query

def updateDistroAndManifests(save_manifests = False, wipe = False):
	print "\nDownloading latest distribution.yaml from"
	distro_q = 'https://api.github.com/repos/ros/rosdistro/contents/indigo/distribution.yaml'
	result = executeQuery(distro_q)
	s = b64decode(result['content'])

	f_path = 'distribution.yaml'
	f = open(f_path, 'w')
	f.write(s)
	f.close()
	print "\nUpdated distro written to ", f_path
	
	print "\nDownloading manifests from GitHub"
	# Can change save path & gitAPI token/email in get_manifests
	if save_manifests == True: 
		Repos_dict = repo.makeReposDict('distribution.yaml')
		saveManifests(Repos_dict, wipe)

if __name__ == '__main__':
	startTime = datetime.now()
	updateDistroAndManifests(save_manifests = True, wipe = True)
	print "\nExecution time: ", (datetime.now()-startTime), '\n'


