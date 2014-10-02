#!/usr/bin/env python

from people import Person, PersonSet
from package import *
from operator import itemgetter
import scorer

import db_exp as dbe
import db_control as dbc


# Takes a string
def jsonifyItem(i):
	return '\t\t\t\t\"' + i + '\"'

# Takes an iterator (over an iterable of strings)
def jsonifyMultiItem(it):
	s = ''
	try:
		s += jsonifyItem(next(it))
		for string in it:
			s += ',\n' + jsonifyItem(string)
		s += '\n'
	except StopIteration:
		pass
	return s;

# Takes a package object
def jsonifyPackage(pkg_id):
	s = ''
	s += '\t\t{\n'

	name = dbe.getSingleVal(cur, 'Packages',['name'],'id',pkg_id)
	s += '\t\t\t\"Name\": \"' + name + '\",\n'

	isMeta = dbe.getSingleVal(cur, 'Packages',['isMetapackage'],'id',pkg_id)
	s += '\t\t\t\"Metapackage\": ' + ('true' if isMeta == 1 else 'false') + ',\n'
	
	dep_ids = dbe.getMatchSet(cur, 'PkgDeps',['dep_id','type_id'],'pkg_id', pkg_id)
	run_key = dbe.getSingleVal(cur,'PkgDepTypes',['id'],'dep_type','run_depend')
	run_ids = set(d[0] for d in dep_ids if d[1] == run_key)
	run_deps = dbe.getSingleValFromSet(cur, 'Packages',['name'],'id',run_ids)
	if isMeta == 1:
		s += '\t\t\t\"Contains\": [\n' # Only used for metapackages
		s += jsonifyMultiItem(iter(run_deps))
		s += '\t\t\t],\n'

	dscrp = dbe.getSingleVal(cur, 'Packages',['description'],'id',pkg_id)
	s += '\t\t\t\"Description\": \"' + dscrp + '\",\n'
	imp = dbe.getSingleVal(cur, 'PkgImpact','impact','pkg_id', pkg_id)
	s += '\t\t\t\"Impact\": ' + str(imp) + ',\n'
	heal = dbe.getSingleVal(cur,'PkgRepoHealth','health','pkg_id', pkg_id)
	s += '\t\t\t\"Health\": ' + str(heal) + ',\n'
	# s += '\t\t\t\"Runtime\": ' + str(p.runtime) + ',\n'

	s += '\t\t\t\"Authors\": [\n'
	author_ids = dbe.getMatchSet(cur,'PkgAuthors',['ppl_id'],'pkg_id', pkg_id)
	author_names = dbe.getSingleValFromSet(cur,'People','name','id',author_ids)
	if None in author_names: author_names.remove(None)
	s += jsonifyMultiItem(iter(author_names))
	s += '\t\t\t],\n'

	s += '\t\t\t\"Maintainers\": [\n'
	mntnr_ids = dbe.getMatchSet(cur,'PkgMntnrs',['ppl_id'],'pkg_id', pkg_id)
	mntnr_names = dbe.getSingleValFromSet(cur,'People','name','id',mntnr_ids)
	if None in mntnr_names: mntnr_names.remove(None)
	s += jsonifyMultiItem(iter(mntnr_names))
	s += '\t\t\t],\n'
	
	s += '\t\t\t\"Edge\": [\n'
	# dep_ids defined above, in case meta
	all_deps = dbe.getSingleValFromSet(cur, 'Packages',['name'],'id',dep_ids)
	s += jsonifyMultiItem(iter(all_deps))
	s += '\t\t\t]\n'
	s += '\t\t}'
	return s

def jsonifyPackages(cur):
	s = ''
	s +='[{\n'
	s += '\t\"id\": \"ros.json\",\n'
	s += '\t\"reports\": [\n'

	pkg_ids = dbe.getTable(cur, 'Packages',['id'])
	for pkg_id in pkg_ids:
		s += ',\n' + jsonifyPackage(pkg_id[0])
	s += '\n'

	s += '\t]\n'
	s += '}]'
	return s

if __name__ == '__main__':
	con,cur = dbc.conCur()
	f = open('ros.json', 'w')
	f.write(jsonifyPackages(cur))
	f.close()
	print('package data written to ros.json')