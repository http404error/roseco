import query_git as qg
import time

# Package only functions:

# Retrieves general information of packages as a list of lists;
# each tuple describes a specific package
def getPkgInfo(packages, info):
	# Keep as a list of lists (not as a list of tuples) because will later need to link
	# each sublist to a repository id
	lol = []
	for idx,p in enumerate(packages.values(), start=1):
		l = [idx] # starts as list, will be converted to tuple and appended
		for inf in info:
			l.append(eval('p.'+inf))
		lol.append(l)

	return lol

# Retrieves package dependencies as a list of tuples, each tuple describes a direct
# dependency relation. There can be many dependency relations for any one package.
def getPkgDeps(pkg_ids, packages):
	lot = []
	for pkg_id in pkg_ids:
		for dep in packages[pkg_id[1]].depend:
			dep_id = [p[0] for p in pkg_ids if p[1] == dep]
			lot.append((pkg_id[0], dep_id[0]))
	return lot
	

# Repo related package functions:

# Creates a list of the unique repository names of all the packages
def getRepoNames(packages):
	l = []
	for p in packages.values():
		if p.vcs_uri != None:
			if 'github' in p.vcs_uri and 'https://github.com/' in p.vcs_uri:
				repo_name = p.vcs_uri.replace('https://github.com/','').replace('.git','')
				if repo_name not in l:
					l.append(repo_name)
		elif p.url != None:
			if 'github' in p.url and 'https://github.com/' in p.url:
				repo_name = p.url.replace('https://github.com/','')
				if repo_name not in l:
					l.append(repo_name)
	return l

# Retrieves the information for each repository's dictionary based on provided keys
def getPkgRepoInfo(repo_names, repo_info_keys):
	lot = []
	for idx,repo_name in enumerate(repo_names, start=1):
		repo_info = qg.getRepoInfo(repo_name, repo_info_keys)
		if repo_info.count(None) == len(repo_info_keys):
			continue # If this repo name is invalid it returns a list of None's
		t = [idx, repo_name] + repo_info
		lot.append(t)
	return lot

# Links the package information with a repository ID if available
def linkPkgInfo2Repo(packages, pkg_info, repo_ids):
	# Pkg infor list is now a list of tuples because there are no other links to add
	lot = []
	for pkg in pkg_info:
		linked = False
		for repo_id in repo_ids:
			if packages[pkg[1]].vcs_uri != None:
				if repo_id[1]+'.git' in packages[pkg[1]].vcs_uri:
					pkg.append(repo_id[0])
					lot.append(tuple(pkg))
					linked = True
					break
			elif packages[pkg[1]].url != None:
				if repo_id[1] in packages[pkg[1]].url:
					pkg.append(repo_id[0])
					lot.append(tuple(pkg))
					linked = True
					break

		if linked == False:
			pkg.append(None)
			lot.append(tuple(pkg))
	
	return lot



# Issues related repo functions:

def getReposIssues(repo_ids, issues_info_keys):
	repos_issues_info = []
	# Can't enumerate bc of for loop structure, use count var
	c = 1
	for repo_id in repo_ids:
		issues_info = qg.getIssuesInfo(repo_id[1], issues_info_keys)
		for issue_info in issues_info:
			if issue_info == None: # This repo name is invalid, don't append anything
				break
			issue_info.insert(0,c)
			c += 1
			issue_info.append(repo_id[0])
			repos_issues_info.append(tuple(issue_info))
	return repos_issues_info


# People related package functions:

def getPkgPpl(packages):
	mntnrs = reduce(set.union, [p.maintainers.people for p in packages.values()])
	authors = reduce(set.union, [p.authors.people for p in packages.values()])
	people = mntnrs.union(authors)

	return people

# Retrieves general information of people based on package dict (maintainers or authors),
# as a list of tuples; each tuple describes a specific person
def getPplInfo(packages, people, info):
	lot = []
	for idx,p in enumerate(people, start=1):
		l = [idx]
		for i in info:
			if i == 'email':
				s = str(eval('p.'+i+'s'))[3:].strip("([''])") # get rid of set string format
				if len(s) == 0: l.append(None) # empty set means no email
				else: l.append(s)
			else:
				l.append(eval('p.'+i))
		lot.append(tuple(l))
	return lot

# Retrieves package maintainers/authors as a list of tuples, each tuple describes a package 
# maintainer/author. There can be many maintainers/authors for any one package
def getPkgAMs(pkg_ids, ppl_ids, packages):
	a_lot = []
	m_lot = []
	for pkg_id in pkg_ids:
		for ppl_id in ppl_ids:
			if packages[pkg_id[1]].authors.find(ppl_id[1]) != None:
				a_lot.append(tuple((pkg_id[0],ppl_id[0])))
			if packages[pkg_id[1]].maintainers.find(ppl_id[1]) != None:
				m_lot.append(tuple((pkg_id[0],ppl_id[0])))
	return a_lot, m_lot


if __name__ == '__main__':
	issues_info_keys = [['user', 'login'], ['assignee', 'login'],'created_at', 'closed_at', 
	                    ['labels', 'name']]
	print getReposIssues( ((1, 'ros-interactive-manipulation/household_objects_database_msgs'),) , issues_info_keys)