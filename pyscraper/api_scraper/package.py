#!/usr/bin/env python

import os
import sys
import re
import random

# YAML parsing
import yaml
# Unicode converting
from unidecode import unidecode

from people import Person, PersonSet

# Not importing until everything else works
# import komodo

# Holds all of the information for a single ROS package
class Package:
	def __init__(self, name):
		self.name = name
		self.package_type = None
		self.license = None
		self.description = None

		self.authors = PersonSet()
		self.maintainers = PersonSet()

		self.maintainer_status = None
		self.url = None
		self.vcs_uri = None
		self.vcs_version = None

		# Used in package scoring
		self.impact = 0.0;
		self.health = 0.0;
		self.runtime = 0.0;

		# Direct dependecy could be run, build, or buildtool, all are treated as equal 
		# in YAML manifests. Only need direct deps because indirect handled in sql selects
		self.depend = set()

	# this shouldn't change much
	def __str__(self):
		s = self.name

		# Authors
		s += '\n  authors:'
		for author in self.authors.people:
			s += '\n    ' + author.name

		# Maintainers
		s += '\n  maintainers:'
		for maintainer in self.maintainers.people:
			s += '\n    ' + maintainer.name

		s += '\n licences: ' + self.license
		s += '\n url: ' + self.url
		s += '\n vcs_uri: ' + self.vcs_uri


		s += '\n  dependencies:'
		s += self._show_number(self.depend)

		return s

	def _show_set(self, name, s):
		retval = '\n  {0}: '.format(name)
		for element in s:
			retval += '\n    ' + element
		return retval

	def _show_number(self, s):
		return '\n    {0}'.format(len(s))

	def getAllDepend(self):
		return self.depend


# Generates a list of all package manifest file paths
# Takes in the path of a folder that contains solely package manifest files
def makeManifestFileList(dir_path):
	if dir_path[-1] != '/': dir_path = dir_path + '/'
	manifests = os.listdir(dir_path)
	manifests[:] = [dir_path + m for m in manifests]
	
	print ' Found', len(manifests), 'manifest files in', dir_path[:-1]
	
	# Take random sample of manifests for testing
	size = 5
	return [manifests[i] for i in random.sample(xrange(len(manifests)),size)]

	return manifests


# Generate a dictionary of all the packages.  Key is the package name,
# value is a Package instance with all of the information filled in.
def makePackageDict(dir_path):
	package_list = []
	package_dict = {}

	# komodo_dict = komodo.makeDataList('./komodo')
	c = 0
	# Parse the files one by one
	for f in makeManifestFileList(dir_path):
		try:
			with open(f, 'r') as open_file:
				manifest = yaml.load(open_file)
		except:
			print '  Bad parse:', f
		

		# Extract the information
		try:
			# YAML files lack name tag, get name from filename, make Package object with name
			name = f[f.find(dir_path)+len(dir_path)+1:f.find('.yaml')]
			package = Package(name)
			package.package_type = extractKey(manifest, 'package_type')

			for person in extractPeople(manifest, 'authors'):
				package.authors.add(person)

			for person in extractPeople(manifest, 'maintainers'):
				package.maintainers.add(person)
			
			package.maintainer_status = extractKey(manifest, 'maintainer_status')
			package.license = extractKey(manifest, 'license')
			package.description = extractKey(manifest, 'description')
			package.url = extractKey(manifest, 'url')
			package.vcs_uri = extractKey(manifest, 'vcs_uri')
			package.vcs_version = extractKey(manifest, 'vcs_version')

			# Set of packages that this package depends on
			package.depend = extractKey(manifest, 'depends')

			# if (package.name in komodo_dict):
			# 	package.runtime = komodo_dict[package.name]

			package_list.append(package)
			package_dict[package.name] = package

		except:
			print '  Parse problem in', f
			sys.exit()

	# Calculate reverse dependencies for each package
	# Although most are listed under the depends_on key there are pkgs missed
	print "  Removing invalid dependencies"
	for p in package_list:
		
		# Clone p's dependencies so that we can remove invalid depndencies when looping
		clone_depend = p.depend.copy()
		for d in clone_depend:
			if d not in package_dict:
				# This dependency isn't in the packages dict and most likely not a package at all
				p.depend.remove(d)

	return package_dict


# Extract valye of a key of from a YAML dict. Key may not exist
def extractKey(manifest, dict_key):
	try:
		val = manifest[dict_key]
		# special dict key cases
		if dict_key == 'depends' or dict_key == 'depends_on':
			val = set(val)
		elif dict_key == 'description':
			val = val.strip().replace('\n','').replace('\r','').replace('\t','').replace('"','').replace('  ','')
			val = re.sub('<[^<]+?>', '', val)
		
		# avoid returning an empty string for a pkg that has the key but no value
		if type(val) == type('str') and len(val) == 0:
			return

		return val
	except:
		if dict_key == 'depends' or dict_key == 'depends_on':
			# For deps and reverse deps return an empty set
			return set()
		else:
			# Returns None (most attribue's default value) if the key doesn't exist
			return


# Extract people (authors or maintainers) from a YAML dict. 
# People-type is the key, and may not exist, or may have an empty string as value
def extractPeople(manifest, people_type):
	Person_list = [] # list of Person objects
	try:
		ppl_str = manifest[people_type]
		ppl_list = ppl_str.split(',')
	except: # no maintainer or author key
		return Person_list

	if len(ppl_list) == 0: # no listed maintainer or author but has key
		return Person_list

	for p_str in ppl_list:
		name = ''
		email = ''
		open_b = p_str.find('<')
		
		if open_b != -1:
			email = p_str[open_b+1:p_str.find('>')]
			name = p_str[:open_b].strip() # name is what's not the email
		else:
			name = p_str.strip() # hopefully this person's string (p_str) is a name
		
		if len(name) != 0:
			# Handle some annoying cases with names
			name = name.replace('Maintained by ', '')
			if type(name) == type(u'unicode'): name = unidecode(name)

			person = Person(name) 
			if len(email) != 0:
				# Turns out some people have unicode emails too...
				if type(email) == type(u'unicode'): email = unidecode(email)
				person.addEmail(email)
			Person_list.append(person)
		elif len(email) != 0:
			person = Person(email) # if no name but an email use it as name
			person.addEmail(email) # and add the email
			Person_list.append(person)

	return Person_list

if __name__ == '__main__':
	packages = makePackageDict('./manifests')
	for p in packages.values():
		if p.name == 'amcl':
			print p.description