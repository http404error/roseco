import get_manifests
import package
import extractor
import scorer
import db_control as dbc

import sys
from datetime import datetime

def getManifests(hydro_api, dir_path):
	# Redownload all manifest files
	print "\nDownloading manifests"
	get_manifests.retrievePkgManifests(url = hydro_api, dir_path = dir_path)

if __name__ == '__main__':
	startTime = datetime.now()





	# getManifests(hydro_api = 'http://docs.ros.org/hydro/api/', dir_path = '/nfs/attic/smartw/users/reume04/roseco/pyscraper/yaml_manifest_scraper/manifests')	

	# Recreate package objects dictionary from manifests and a set of all people
	print "Retrieving packages and people"
	packages = package.makePackageDict('./manifests')
	people = extractor.getPkgPpl(packages)

	# Establish remote database connection
	print "\nConnecting to database"
	con, cur = dbc.conCur(user='dbuser',passwd='dbpass',db='test2',host='localhost',port=None)



	# Define what information will be extracted for pkgs & ppl and subsequently the column names
	pkg_cols = ['name','package_type','license','description', 'maintainer_status',
	            'url','vcs_uri','vcs_version']
	ppl_cols = ['name','email']
	# Extract desired information
	pkg_info = extractor.getPkgInfo(packages, pkg_cols)
	ppl_info = extractor.getPplInfo(packages, people, ppl_cols)
	# Append the id column to the front of the col lists
	pkg_cols.insert(0,'id')
	ppl_cols.insert(0,'id')
	# Define table column data types, update table changes col types if they differ, includes id
	pkg_types = ['SMALLINT(6)','VARCHAR(100)','VARCHAR(50)','VARCHAR(100)','VARCHAR(700)', 
				 'VARCHAR(20)','VARCHAR(80)','VARCHAR(90)', 'VARCHAR(50)']
	ppl_types = ['SMALLINT(6)','VARCHAR(100)','VARCHAR(50)']
	



	# Information tables:


	# Update the People table, an isoalted table
	print "\nUpdating People table"
	dbc.updateTable(con=con, cur=cur, table='People3', col_names=ppl_cols,
		            col_types=ppl_types, data=ppl_info)




	# Set up Repos table first, to link with Packages table after
	# Retrieve all unique repository names of all the packages
	print "\nRetrieving repository information"
	repo_names = extractor.getRepoNames(packages)
	# Define the keys that specify what values will be retrieved for each repository
	repo_keys = [['owner', 'type'], 'created_at', 'updated_at', 'pushed_at', 
	                  'size', 'forks_count', 'watchers_count', 'subscribers_count']
	repo_info = extractor.getPkgRepoInfo(repo_names, repo_keys)
	# Define the column names and types for the Repos table, includes id
	repo_cols = ['id','name','owner_type','created_at','updated_at','pushed_at',
	             'size','forks_count','watchers_count','subscribers_count']
	repo_types = ['SMALLINT(6)','VARCHAR(60)','VARCHAR(30)','CHAR(10)','CHAR(10)',
	              'CHAR(10)','MEDIUMINT(9)','SMALLINT(6)','SMALLINT(6)','SMALLINT(6)']
	# Create the Repos table
	print "Updating Repos table"
	dbc.updateTable(con=con,cur=cur, table='Repos', col_names=repo_cols, 
	                col_types=repo_types, data=repo_info)




	# Set up to link Repos table with Packages table
	# Retrieve repository primary key id and name
	repo_ids = dbc.getTable(cur=cur, table='Repos', cols=['id','name'], row_max=repo_info[-1][0])
	# Link the repository id to the package info and and add foreign key to pkg_cols/types
	pkg_info = extractor.linkPkgInfo2Repo(packages, pkg_info, repo_ids)
	pkg_cols.append('repo_id')
	pkg_types.append('SMALLINT(6)')
	# Create the Packages table linked to Repos
	print "\nUpdating Packages table, linked to Repos, of row size:", len(pkg_info)
	dbc.updateTable(con=con, cur=cur, table='Packages', col_names=pkg_cols, 
		            col_types=pkg_types, data=pkg_info, fkey_ref='Repos(id)')




	# Set up to link Repos table with Issues table
	issues_info_keys = [['user', 'login'], ['assignee', 'login'],'created_at', 'closed_at', 
	                    ['labels', 'name']]
	print "\nRetrieving repository issues"
	issues_info = extractor.getReposIssues(repo_ids, issues_info_keys)
	issue_cols = ['id', 'created_by','assigned_to','created_at','closed_at','labels','repo_id']
	issue_types = ['MEDIUMINT(9)','VARCHAR(50)','VARCHAR(50)','CHAR(10)','CHAR(10)','VARCHAR(100)','SMALLINT(6)']
	print "Updating Issues table, linked to Repos"
	dbc.updateTable(con=con,cur=cur, table='Issues', col_names=issue_cols,
		            col_types=issue_types,data=issues_info,fkey_ref='Repos(id)')



	# Establish row maxs for linking and scoring tables
	pkg_row_max = pkg_info[-1][0]
	ppl_row_max = ppl_info[-1][0]
	repo_row_max = repo_info[-1][0]


	
	# Link Packages table to People through mapping tables, and Packages to Packages
	# Retrieve package/people primary key id and name
	pkg_ids = dbc.getTable(cur=cur, table='Packages', cols=['id','name'], row_max=pkg_row_max)
	ppl_ids = dbc.getTable(cur=cur, table='People', cols=['id','name'], row_max=ppl_row_max)
	# Use primary keys of Packages and People to generate foreign key pairings
	pkg_deps = extractor.getPkgDeps(pkg_ids, packages)
	pkg_authors, pkg_mntnrs = extractor.getPkgAMs(pkg_ids, ppl_ids, packages)
	# Create the foreign key mapping tables
	print "\nCreating PkgDeps table, mapping table for Packages, of row size:", len(pkg_deps)
	dbc.makeMapTable(con=con,cur=cur, table='PkgDeps', key_names=['pkg_id','dep_id'],
		             key_refs=['Packages(id)','Packages(id)'], data=pkg_deps)
	print "Creating PkgAuthors and PkgMntnrs tables, mapping tables for Packages and People"
	dbc.makeMapTable(con=con,cur=cur, table='PkgAuthors', key_names=['pkg_id','ppl_id'],
		             key_refs=['Packages(id)','People(id)'], data=pkg_authors)
	dbc.makeMapTable(con=con,cur=cur, table='PkgMntnrs', key_names=['pkg_id','ppl_id'],
		             key_refs=['Packages(id)','People(id)'], data=pkg_mntnrs)





	# Scoring tables:


	# Score packages on impact
	pkg_only_ids = dbc.getTable(cur=cur, table='Packages', cols=['id'], row_max=pkg_row_max)
	repo_only_ids = dbc.getTable(cur=cur, table='Repos', cols=['id'], row_max=repo_row_max)
	ppl_only_ids = dbc.getTable(cur=cur, table='People', cols=['id'], row_max=ppl_row_max)
	


	print "\nScoring package impact"
	pkg_impact = scorer.getPkgsImpact(pkg_only_ids, cur)
	print "\nScoring package health"
	pkg_health = scorer.getPkgsHealth(pkg_only_ids, cur)
	print "\nScoring repo health"
	repo_health = scorer.getReposHealth(repo_only_ids, cur)



	print "\nCreating PkgImpact table, linked to Packages"
	dbc.makeScoreTable(con=con, cur=cur, table='PkgImpact', col_names=['pkg_id','impact'], 
		                col_types=['SMALLINT(6)','FLOAT'],fkey_ref='Packages(id)',data=pkg_impact)
	
	print "Creating PkgHealth table, linked to Packages"
	dbc.makeScoreTable(con=con,cur=cur,table='PkgHealth',col_names=['pkg_id','health'],
		               col_types=['SMALLINT(6)','FLOAT'],fkey_ref='Packages(id)',data=pkg_health)

	print "Creating RepoHealth table, linked to Repos"
	dbc.makeScoreTable(con=con,cur=cur,table='RepoHealth',col_names=['repo_id','health'],
		               col_types=['SMALLINT(6)','FLOAT'],fkey_ref='Repos(id)',data=repo_health)



	# Metrics below use the values in the tables above
	print "\nScoring people impact"
	ppl_impact = scorer.getPplImpact(ppl_only_ids, cur)
	print "\nScoring repo package composite health"
	pkg_repo_health = scorer.getPkgsReposHealth(pkg_only_ids, repo_only_ids, cur)
	
	print "\nCreating PplImpact table, linked to People"
	dbc.makeScoreTable(con=con,cur=cur,table='PplImpact',col_names=['ppl_id','impact'],
		               col_types=['SMALLINT(6)','FLOAT'],fkey_ref='People(id)',data=ppl_impact)
	print "Creating PkgRepoHealth table, linked to Packages",
	print ", a weighted combination of PkgHealth and RepoHealth scores"
	dbc.makeScoreTable(con=con,cur=cur,table='PkgRepoHealth',col_names=['pkg_id','health'],
		               col_types=['SMALLINT(6)','FLOAT'],fkey_ref='Packages(id)',data=pkg_repo_health)





	print "\nExecution time: ", (datetime.now()-startTime), '\n'