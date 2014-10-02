import repo

import requests
from requests.auth import HTTPBasicAuth

import json
from base64 import b64decode
import xml.etree.ElementTree as ET
from unidecode import unidecode

import os
from sys import exit

# Github authentification
token = 'c201b0b14cbf8ec976afa94e3b2cc45f456b3260'
email = 'twthornt@colby.edu'

# Manifest saving directory
dir_path = '/nfs/attic/smartw/users/reume04/roseco/pyscraper/indigo_scraper/manifests'


def makeContentsQuery(repo_url):
	repo_owner = repo_url.replace('https://github.com/','').replace('.git','')
	query = 'https://api.github.com/repos/' + repo_owner + '/contents'
	return query

def executeQuery(query):
	req = requests.get(query, auth=HTTPBasicAuth(email, token))
	result = json.loads(req.text)
	
	if 'message' in result: # Message key only in result if 'Not Found'
		print 'Failed Query:', query
		return
	
	return result

# Recursively traverse directories of repositories for manifests
def getManifests(query):
	contents = executeQuery(query)
	manifests = []
	
	# If contents query failed return empty list rather than None
	# in order to prevent any looping by the for loop that uses the result
	if contents == None: return manifests

	for item in contents:
		if item['type'] == 'file' and item['name'] == 'package.xml':
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
				decoded = unidecode(result)
				manifest.find(ptype).text = decoded

	return manifest

def saveManifests(Repo_dict):
	# To overwrite all files with updated manifests
	# initialize the file_names as an empty list
	# file_names = []
	
	file_names = os.listdir(dir_path)
	
	for key,repo in Repo_dict.items():

		for repo_url in repo.urls:
			query = makeContentsQuery(repo_url)
			manifests = getManifests(query)
			
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
						print "Saved:", file_name
					except:
						print "\nFailed save:", file_name, "\nfrom repo:", query

if __name__ == '__main__':
	Repo_dict = repo.makeReposDict('distribution.yaml')
	saveManifests(Repo_dict)