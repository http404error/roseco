import repo
import package

import get_manifests
import extractor
import scorer

import db_control as dbc
import db_extract as dbe

import json_exp_db as j_exp

import sys
from datetime import datetime

def update():
	print "Updating Repos dictionary"
	Repos_dict = repo.makeReposDict('distribution.yaml')
	
	print "\nDownloading manifests"
	# Can change save path & gitAPI token/email in get_manifests
	# get_manifests.saveManifests(Repos_dict)

	# Recreate package objects dictionary from manifests and a set of all people
	print "Retrieving packages and people"
	packages = package.makePackageDict('./manifests', Repos_dict)
	people = extractor.allPkgPpl(packages)

	# Establish remote database connection
	print "\nConnecting to database"
	con, cur = dbc.conCur(user='dbuser',passwd='dbpass',db='test3',host='localhost',port=None)



	# Define what information will be extracted for pkgs & ppl and subsequently the column names
	pkg_cols = ['name','isMetapackage','description','wiki']
	ppl_cols = ['name','emails']
	# Extract desired information
	pkg_info = extractor.getPkgInfo(packages, pkg_cols)
	pkg_row_max = pkg_info[-1][0] # Row maxes for mapping tables
	ppl_info = extractor.getPplInfo(packages, people, ppl_cols)
	ppl_row_max = ppl_info[-1][0]
	# Append the id column to the front of the col lists
	pkg_cols.insert(0,'id')
	ppl_cols.insert(0,'id')
	# Define table column data types, update table changes col types if they differ, includes id
	pkg_types = ['SMALLINT(6)','VARCHAR(100)','TINYINT(1)','VARCHAR(650)','VARCHAR(100)']
	ppl_types = ['SMALLINT(6)','VARCHAR(150)','VARCHAR(50)']
	
	


	# Information tables:


	
	# Update the Packages table, no foreign keys
	print "\nUpdating Packages table, rows:", len(pkg_info)
	dbc.upTruncTable(con, cur, 'Packages', pkg_cols, pkg_types, pkg_info,
		            pk='id')
	sys.exit()
	# Update the Licenses table, no foreign keys
	licenses = extractor.getLicenses(packages)
	print "\nMaking Licenses table, rows:", len(licenses)
	dbc.upTruncTable(con,cur,'Licenses',['id','name'],
		            ['SMALLINT(6)','VARCHAR(150)'], licenses, pk='id')
	# Update the People table, no foreign keys
	print "\nUpdating People table, rows:", len(ppl_info)
	dbc.upTruncTable(con, cur, 'People', ppl_cols, ppl_types, ppl_info, pk='id')
	


	# Link Packages table to People through mapping tables, and Packages to Packages
	# Retrieve package/people primary key id and name
	pkg_ids = dbe.getTable(cur, 'Packages', ['id','name'], pkg_row_max)
	license_ids = dbe.getTable(cur, 'Licenses',['id','name'])
	ppl_ids = dbe.getTable(cur, 'People', ['id','name'], ppl_row_max)
	# Use primary keys of Packages and People for linking and mapping tables
	dep_type_ids = [(1,'buildtool_depend'),(2,'build_depend'),(3,'run_depend')]
	pkg_deps = extractor.mapPkgDeps(pkg_ids, dep_type_ids, packages)
	pkg_licenses = extractor.mapPkgLicenses(pkg_ids, license_ids, packages)
	pkg_authors, pkg_mntnrs = extractor.mapPkgAMs(pkg_ids, ppl_ids, packages)
	# Create the foreign key mapping or linked tables
	print "Updating PkgDepTypes, dependency key table for PkgDeps"
	dbc.upTruncTable(con,cur,'PkgDepTypes', ['id','dep_type'],
		            ['SMALLINT(6)','VARCHAR(16)'],dep_type_ids,pk='id')
	print "Updating PkgDeps table, mapping table for Packages, rows:", len(pkg_deps)
	dep_cols = ['pkg_id','dep_id','type_id']
	dep_col_t = ['SMALLINT(6)', 'SMALLINT(6)', 'SMALLINT(6)']
	dbc.upTruncTable(con,cur,'PkgDeps',dep_cols,dep_col_t,pkg_deps,fk=dep_cols,
		            fk_ref=['Packages(id)','Packages(id)','PkgDepTypes(id)'])
	print "Updating PkgLicenses table, mapping table for Packages & Licenses, rows:", len(pkg_licenses)
	lic_cols = ['pkg_id','lic_id']
	lic_col_t = ['SMALLINT(6)', 'SMALLINT(6)']
	dbc.upTruncTable(con,cur,'PkgLicenses',lic_cols, lic_col_t, pkg_licenses,
		             fk=lic_cols, fk_ref=['Packages(id)','Licenses(id)'])
	print "Updating PkgAuthors & PkgMntnrs tables, mapping tables for Packages & People"
	am_cols = ['pkg_id','ppl_id']
	am_col_t = ['SMALLINT(6)', 'SMALLINT(6)']
	am_fk_refs = ['Packages(id)','People(id)']
	dbc.upTruncTable(con,cur, 'PkgAuthors', am_cols, am_col_t, pkg_authors,
		             fk = am_cols, fk_ref = am_fk_refs)
	dbc.upTruncTable(con,cur, 'PkgMntnrs', am_cols, am_col_t, pkg_mntnrs,
		             fk = am_cols, fk_ref = am_fk_refs)

	

	# Set up Repos table first, to link with Packages table after
	# Retrieve all unique repository names of all the packages
	print "\nRetrieving repository information"
	repo_names = extractor.getRepoNames(packages)
	# Define the keys that specify what values will be retrieved for each repository
	repo_keys = [['owner', 'type'], 'created_at', 'updated_at', 'pushed_at', 
	              'size', 'forks_count', 'watchers_count', 'subscribers_count']
	repo_info = extractor.getRepoInfo(repo_names, repo_keys)
	repo_row_max = repo_info[-1][0]
	# Define the column names and types for the Repos table, includes id
	repo_cols = ['id','name','owner_type','created_at','updated_at','pushed_at',
	             'size','forks_count','watchers_count','subscribers_count']
	repo_types = ['SMALLINT(6)','VARCHAR(60)','VARCHAR(30)','CHAR(10)','CHAR(10)',
	              'CHAR(10)','MEDIUMINT(9)','SMALLINT(6)','SMALLINT(6)','SMALLINT(6)']
	# Create the Repos table
	print "Updating Repos table, rows:", len(repo_info)
	dbc.upTruncTable(con, cur, 'Repos', repo_cols, repo_types, repo_info, pk='id')



	repo_ids = dbe.getTable(cur, table='Repos', cols=['id','name'], row_max=repo_info[-1][0])
	# Mapping table for Packages and Repos tables, many to many
	pkg_repos = extractor.mapPkgRepos(pkg_ids, repo_ids, packages)
	print "Updating PkgRepos, mapping table for Packages and Repos, rows:", len(pkg_repos)
	pr_cols = ['pkg_id','repo_id']
	pr_types = ['SMALLINT(6)', 'SMALLINT(6)']
	dbc.upTruncTable(con, cur, 'PkgRepos', pr_cols, pr_types, pkg_repos,
		            fk = pr_cols, fk_ref = ['Packages(id)', 'Repos(id)'])
	


	# Set up to make Issues table linked to Repos table
	issues_info_keys = [['user', 'login'], ['assignee', 'login'],'created_at', 'closed_at', 
	                    ['labels', 'name']]
	print "\nRetrieving repository issues"
	issues_info = extractor.getIssuesLinkRepos(repo_ids, issues_info_keys)
	issue_cols = ['id', 'created_by','assigned_to','created_at','closed_at','labels','repo_id']
	issue_cols,issues_info,label_ids,issues_labels = extractor.getIssuesLabels(issue_cols, issues_info)
	issue_types = ['MEDIUMINT(9)','VARCHAR(50)','VARCHAR(50)','CHAR(10)','CHAR(10)','SMALLINT(6)']
	print "Updating Issues table, linked to Repos, rows:", len(issues_info)
	dbc.upTruncTable(con,cur, 'Issues', issue_cols, issue_types, issues_info,
		            pk='id', fk='repo_id', fk_ref='Repos(id)')
	print "Updating Labels table, rows:", len(label_ids)
	dbc.upTruncTable(con, cur, 'Labels', ['id','name'],
		            ['SMALLINT(6)','VARCHAR(20)'], label_ids, pk='id')
	print "Updating IssuesLabels table, rows:", len(issues_labels)
	il_cols = ['issue_id','label_id']
	il_types = ['MEDIUMINT(9)', 'SMALLINT(6)']
	dbc.upTruncTable(con, cur, 'IssuesLabels', il_cols, il_types, issues_labels,
		            fk=il_cols, fk_ref=['Issues(id)','Labels(id)'])
	
	

	# Scoring tables:


	# Score packages on impact
	pkg_only_ids = dbe.getTable(cur, 'Packages', ['id'], pkg_row_max)
	repo_only_ids = dbe.getTable(cur, 'Repos', ['id'], repo_row_max)
	ppl_only_ids = dbe.getTable(cur, 'People', ['id'], ppl_row_max)
	


	print "\nScoring package impact"
	pkg_impact = scorer.getPkgsImpact(pkg_only_ids, cur)
	print "Scoring package health"
	pkg_health = scorer.getPkgsHealth(pkg_only_ids, cur)
	print "Scoring repo health"
	repo_health = scorer.getReposHealth(repo_only_ids, cur)



	print "\nUpdating PkgImpact table, linked to Packages"
	dbc.upTruncTable(con, cur,'PkgImpact',['pkg_id','impact'],
		            ['SMALLINT(6)','FLOAT'], pkg_impact, 
		            fk='pkg_id', fk_ref='Packages(id)')
	
	print "Updating PkgHealth table, linked to Packages"
	dbc.upTruncTable(con, cur, 'PkgHealth', ['pkg_id','health'],
		            ['SMALLINT(6)','FLOAT'], pkg_health,
		            fk='pkg_id', fk_ref='Packages(id)')

	print "Updating RepoHealth table, linked to Repos"
	dbc.upTruncTable(con, cur, 'RepoHealth', ['repo_id','health'],
		            ['SMALLINT(6)','FLOAT'],repo_health,
		            fk='repo_id',fk_ref='Repos(id)')



	# Metrics below use the values in the tables above
	print "\nScoring people impact"
	ppl_impact = scorer.getPplImpact(ppl_only_ids, cur)
	print "Scoring repo package composite health"
	pkg_repo_health = scorer.getPkgsReposHealth(pkg_only_ids, repo_only_ids, cur)
	
	print "\nUpdating PplImpact table, linked to People"
	dbc.upTruncTable(con, cur, 'PplImpact', ['ppl_id','impact'],
		            ['SMALLINT(6)','FLOAT'], ppl_impact, 
		            fk='ppl_id', fk_ref='People(id)')
	print "Updating PkgRepoHealth table, linked to Packages",
	print "a weighted combination of PkgHealth and RepoHealth scores"
	dbc.upTruncTable(con, cur, 'PkgRepoHealth', ['pkg_id','health'],
		            ['SMALLINT(6)','FLOAT'],pkg_repo_health, 
		            fk = 'pkg_id', fk_ref = 'Packages(id)')

	print "Writing package data to ros.json"
	f = open('ros.json', 'w')
	f.write(j_exp.jsonifyPackages(cur))
	f.close()

if __name__ == '__main__':
	startTime = datetime.now()
	update()
	print "\nExecution time: ", (datetime.now()-startTime), '\n'