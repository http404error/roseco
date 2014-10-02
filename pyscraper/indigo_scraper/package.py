#!/usr/bin/env python

from os import listdir
from sys import exit
from re import sub
import random

from unidecode import unidecode
import xml.etree.ElementTree as ET

from people import Person, PersonSet
import repo

# Not importing until everything else works
# import komodo

# Holds all of the information for a single ROS package
class Package:
	def __init__(self, name, repo):
		self.name = name
		self.repo = repo

		self.authors = PersonSet()
		self.maintainers = PersonSet()

		self.isMetapackage = False
		self.description = ''
		self.licenses = None
		self.wiki = None # Not storing non-wiki urls (ex: git) bc stored in repo

		# Package dependencies
		self.buildtool_depend = None
		self.build_depend = None
		self.run_depend = None

		# # Package scoring
		# self.impact = 0.0;
		# self.health = 0.0;
		# self.runtime = 0.0;

	def __str__(self):
		s = self.name

		s += '\n  authors:'
		for author in self.authors.people:
			s += '\n    ' + author.name
		s += '\n  maintainers:'
		for maintainer in self.maintainers.people:
			s += '\n    ' + maintainer.name

		s += self._show_set('licences', self.licenses)
		s += '\n  dependencies:'
		s += '\n   buildtool ' + str(len(self.buildtool_depend))
		s += '\n   build ' + str(len(self.build_depend))
		s += '\n   run ' + str(len(self.run_depend))

		return s

	def _show_set(self, name, s):
		retval = '\n  {0}: '.format(name)
		for element in s:
			retval += '\n    ' + element
		return retval

	def getAllDepend(self):
		return self.buildtool_depend | self.build_depend | self.run_depend

# Generates a list of all package manifest file paths
# dir_path is a folder containing solely package manifest files
def makeManifestFileList(dir_path):
	if dir_path[-1] != '/': dir_path = dir_path + '/'
	manifests = listdir(dir_path)
	manifests[:] = [dir_path + m for m in manifests]
	print ' ', len(manifests), 'manifest files in', dir_path[:-1]
	
	# Take random sample of manifests for testing
	# size = 10
	# return [manifests[i] for i in random.sample(xrange(len(manifests)),size)]

	return manifests

# Generate a dictionary of all the packages.  Key is the package name,
# value is a Package instance with all of the information filled in.
def makePackageDict(dir_path, Repos_dict):
	package_dict = {}
	# komodo_dict = komodo.makeDataList('./komodo')
	
	# Parse the files one by one
	for f in makeManifestFileList(dir_path):
		with open(f, 'r') as open_file:
			tree = ET.parse(open_file)

		root = tree.getroot()
		name = root.find('name').text
		repo = Repos_dict[f[f.rindex('/')+1:f.rindex('-')]]
		package = Package(name, repo)

		for person in extractPeople(root, 'author'):
			package.authors.add(person)
		for person in extractPeople(root, 'maintainer'):
			package.maintainers.add(person)

		if '<metapackage' in ET.tostringlist(root): 
			package.isMetapackage = True
			print "   Found metapackage", name
		predescription = extractTag(root, 'description')[0].strip().replace('\n','').replace('\r','').replace('\t','').replace('"','').replace('  ','')
		package.description = sub(r'<.+?>', '', predescription)
		package.licenses = set(extractTag(root, 'license'))
		prewiki = extractTag(root, 'url')
		if prewiki != None and None not in prewiki: prewiki = [url for url in prewiki if 'wiki'in url and 'git' not in url]
		if len(prewiki) > 0: package.wiki = prewiki[0]

		package.buildtool_depend = set(extractTag(root, 'buildtool_depend'))
		package.build_depend = set(extractTag(root, 'build_depend'))
		package.run_depend = set(extractTag(root, 'run_depend'))

		# if (package.name in komodo_dict):
		# 	package.runtime = komodo_dict[package.name]

		package_dict[package.name] = package
	
	# Calculate reverse dependencies for each package
	# Although most are listed under the depends_on key there are pkgs missed
	print "   Verifying dependencies:",
	counts = [0,0]
	for p in package_dict.values():
		deps = [p.buildtool_depend, p.build_depend, p.run_depend]
		for dep in deps:
			clone_depend = dep.copy() # Clone these deps to remove invalids when looping
			for d in clone_depend:
				if d not in package_dict:
					dep.remove(d) # Remove deps that are not known packages
					counts[0] += 1
				else: counts[1] += 1
	print "   Invalid ", counts[0],
	print "   Valid ", counts[1]
	return package_dict

def extractTag(root, tag):
	return [elem.text for elem in root.findall(tag)]

def extractPeople(root, tag):
	people = []
	for p in root.findall(tag):
		person = Person(p.text)
		email = p.get('email')
		if email != None: person.addEmail(email)
		people.append(person)
	return people

if __name__ == '__main__':
	from datetime import datetime
	Repos_dict = repo.makeReposDict('distribution.yaml')
	startTime = datetime.now()
	packages = makePackageDict('./manifests', Repos_dict)
	print "\nExecution time: ", (datetime.now()-startTime), '\n'
	# for p in packages.values():
		# for m in p.maintainers:
		# 	print m.emails
		# for a in p.authors:
		# 	print a.emails