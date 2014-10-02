#!/usr/bin/env python

from people import Person, PersonSet
from package import *
from operator import itemgetter
import scorer

import db_extract as dbe
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
def jsonifyPackage(pkg_id, cur):
	s = ''
	s += '\t\t{\n'

	name = dbe.getMatchVal(cur, 'Packages',['name'],'id',pkg_id)
	s += '\t\t\t\"Name\": \"' + name + '\",\n'

	isMeta = dbe.getMatchVal(cur, 'Packages',['isMetapackage'],'id',pkg_id)
	s += '\t\t\t\"Metapackage\": ' + ('true' if isMeta == 1 else 'false') + ',\n'
	
	dep_ids = dbe.getMatchSet(cur, 'PkgDeps',['dep_id','type_id'],'pkg_id', pkg_id)
	run_key = dbe.getMatchVal(cur,'PkgDepTypes',['id'],'dep_type','run_depend')
	run_ids = set(d[0] for d in dep_ids if d[1] == run_key)
	run_deps = dbe.getMatchValFromSet(cur, 'Packages',['name'],'id',run_ids)
	if isMeta == 1:
		s += '\t\t\t\"Contains\": [\n' # Only used for metapackages
		s += jsonifyMultiItem(iter(run_deps))
		s += '\t\t\t],\n'

	dscrp = dbe.getMatchVal(cur, 'Packages',['description'],'id',pkg_id)
	s += '\t\t\t\"Description\": \"' + dscrp + '\",\n'
	
	wiki = dbe.getMatchVal(cur, 'Packages',['wiki'],'id',pkg_id)
	if wiki is None: wiki = ''
	s += '\t\t\t\"Wiki\": \"' + wiki + '\",\n'
	
	imp = dbe.getMatchVal(cur, 'PkgImpact','impact','pkg_id', pkg_id)
	s += '\t\t\t\"Impact\": ' + str(imp) + ',\n'
	heal = dbe.getMatchVal(cur,'PkgRepoHealth','health','pkg_id', pkg_id)
	s += '\t\t\t\"Health\": ' + str(heal) + ',\n'
	
	runtime = dbe.getMatchVal(cur, 'Packages', ['runtime'],'id',pkg_id)
	s += '\t\t\t\"Runtime\": ' + str(runtime) + ',\n'

	s += '\t\t\t\"Repos\": [\n'
	repo_ids = dbe.getMatchSet(cur,'PkgRepos',['repo_id'],'pkg_id', pkg_id)
	repo_names = dbe.getMatchValFromSet(cur,'Repos','name','id',repo_ids)
	s += jsonifyMultiItem(iter(repo_names))
	s += '\t\t\t],\n'

	s += '\t\t\t\"Authors\": [\n'
	author_ids = dbe.getMatchSet(cur,'PkgAuthors',['ppl_id'],'pkg_id', pkg_id)
	author_names = dbe.getMatchValFromSet(cur,'People','name','id',author_ids)
	if None in author_names: author_names.remove(None)
	s += jsonifyMultiItem(iter(author_names))
	s += '\t\t\t],\n'

	s += '\t\t\t\"Maintainers\": [\n'
	mntnr_ids = dbe.getMatchSet(cur,'PkgMntnrs',['ppl_id'],'pkg_id', pkg_id)
	mntnr_names = dbe.getMatchValFromSet(cur,'People','name','id',mntnr_ids)
	if None in mntnr_names: mntnr_names.remove(None)
	s += jsonifyMultiItem(iter(mntnr_names))
	s += '\t\t\t],\n'
	
	s += '\t\t\t\"Edge\": [\n'
	# dep_ids defined above, in case meta
	all_deps = dbe.getMatchValFromSet(cur, 'Packages',['name'],'id',dep_ids)
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
	s += jsonifyPackage(pkg_ids[0][0], cur)
	for pkg_id in pkg_ids[1:]:
		s += ',\n' + jsonifyPackage(pkg_id[0], cur)
	s += '\n'

	s += '\t]\n'
	s += '}]'
	return s

if __name__ == '__main__':
	con,cur = dbc.conCur()
	# f_path = '/nfs/attic/smartw/users/reume04/roseco/pyscraper/rostest.json'
	f_path = 'ros.json'
	f = open(f_path, 'w')
	f.write(jsonifyPackages(cur))
	f.close()
	print('package data written to ros.json')