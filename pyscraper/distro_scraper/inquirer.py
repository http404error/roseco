import db_extract as dbe
import db_control as dbc 

con, cur = dbc.conCur(db='ROSdb')

def inquire(quest, cmd, cur=cur):
	answer = dbe.exFetch(cur, cmd, single = True)
	return '\n{0}\t{1}\n\t{2}'.format(quest, answer, cmd)

def inquire(quest, cmd, cur=cur):
	answer = dbe.exFetch(cur, cmd, single = True)
	return '\n{0}\t{1}\n\t{2}'.format(quest, answer, cmd)

def buildString():
	s = ''

	# Important ones
	s += inquire('For this distribution, what is the sum of all ROS repositories in kilobytes?', 
		"SELECT SUM(size) FROM eco_Repos")
	s += inquire('How many of the packages have a BSD license?',
		"SELECT COUNT(DISTINCT eco_PkgLicenses.pkg_id) FROM eco_PkgLicenses, eco_Licenses WHERE lic_id = eco_Licenses.id AND eco_Licenses.name = 'BSD'")
	s += inquire('How many different GitHub users have opened an issue on a ROS repo?',
		"SELECT COUNT(*) FROM eco_GitUsers")
	s += inquire('What is the average days since a eco_Repository was updated?',
		"SELECT AVG(DATEDIFF(CURRENT_DATE, updated_at)) FROM eco_Repos")
	s += inquire('Which packages is most commonly listed as a run dependency?',
		"SELECT eco_Packages.name, eco_PkgDeps.dep_id, COUNT(*) FROM eco_PkgDeps, eco_Packages WHERE eco_Packages.id = eco_PkgDeps.dep_id AND eco_PkgDeps.type_id = 3 GROUP BY dep_id ORDER BY COUNT(*) DESC LIMIT 1")
	s += inquire('How many packages are there per maintainer?',
		"SELECT COUNT(DISTINCT eco_Packages.id)/COUNT(DISTINCT eco_PkgMntnrs.ppl_id) FROM eco_Packages, eco_PkgMntnrs")

	s += inquire('How many total open Issues are there on ROS repos?',
		"SELECT COUNT(*) FROM eco_Issues WHERE closed_at IS NULL")
	s += inquire('How many open Issues are unassigned?',
		"SELECT COUNT(*) FROM eco_Issues WHERE closed_at IS NULL AND assigned_to IS NULL")
	s += inquire('Which Repository has the most open Issues?',
		"SELECT eco_Repos.name, eco_Issues.repo_id, SUM(if(eco_Issues.closed_at IS NULL, 1, 0)) AS c FROM eco_Issues, eco_Repos WHERE eco_Repos.id = eco_Issues.repo_id GROUP BY repo_id ORDER BY c DESC LIMIT 1")
	s += inquire('Which package has the lowest health with a substantial impact?',
		"SELECT eco_Packages.name FROM eco_Packages, eco_PkgImpact, eco_PkgRepoHealth WHERE eco_PkgImpact.impact > 0.35 AND eco_Packages.id = eco_PkgRepoHealth.pkg_id ORDER BY eco_PkgRepoHealth.health DESC LIMIT 1")

	s += '\n\n'

	s += inquire('How many different GitHub users have opened an issue on a ROS repo?',
		"SELECT COUNT(*) FROM eco_GitUsers")
	s += inquire('Which GitHub user has the highest activity score?',
		"SELECT eco_GitUsers.username FROM eco_GitUsers, eco_GitActivity WHERE eco_GitActivity.git_id = eco_GitUsers.id AND eco_GitActivity.activity = 1.0")
	s += inquire('How many GitHub users (with listed email) are also maintainers/authors',
		"SELECT COUNT(*) FROM eco_GitPpl")
	s += inquire('Which GitHub user and Package Person has the highest impactivity score?',
		"SELECT eco_People.name FROM eco_People, eco_GitPpl, eco_GitPplImpactivity WHERE eco_People.id = eco_GitPpl.ppl_id AND eco_GitPpl.id = eco_GitPplImpactivity.git_ppl_id AND eco_GitPplImpactivity.impactivity = 1.0")
	
	s += '\n'
	s += inquire('How many total open Issues are there on ROS repos?',
		"SELECT COUNT(*) FROM eco_Issues WHERE closed_at IS NULL")
	s += inquire('How many open eco_Issues are unassigned?',
		"SELECT COUNT(*) FROM eco_Issues WHERE closed_at IS NULL AND assigned_to IS NULL")
	s += inquire('Which Repository has the most open Issues?',
		"SELECT eco_Repos.name, eco_Issues.repo_id, SUM(if(eco_Issues.closed_at IS NULL, 1, 0)) AS c FROM eco_Issues, eco_Repos WHERE eco_Repos.id = eco_Issues.repo_id GROUP BY repo_id ORDER BY c DESC LIMIT 1")
	s += inquire('What is most commonly used Issues label?',
		"SELECT eco_Labels.name, eco_IssuesLabels.label_id FROM eco_Labels, eco_IssuesLabels WHERE eco_IssuesLabels.label_id = eco_Labels.id GROUP BY eco_IssuesLabels.label_id ORDER BY COUNT(eco_IssuesLabels.label_id) DESC LIMIT 1")

	s += '\n'
	s += inquire('How large is ROS in kilobytes?', 
		"SELECT SUM(size) FROM eco_Repos")
	s += inquire('How large is ROS, excluding release eco_Repos? (in KB)',
		"SELECT SUM(size) FROM eco_Repos WHERE name NOT LIKE '%release%'")
	s += inquire('How many Repositories are there?',
		"SELECT COUNT(*) FROM eco_Repos")
	s += inquire('How many of those are owned by organizations?',
		"SELECT COUNT(*) FROM eco_Repos WHERE owner_type = 'Organization'")
	s += inquire('How many of those are owned by single users',
		"SELECT COUNT(*) FROM eco_Repos WHERE owner_type = 'User'")
	s += inquire('What is the average age of a Repository',
		"SELECT DATE_FORMAT(FROM_DAYS(AVG(DATEDIFF(CURRENT_DATE, created_at))),'%y-%m-%d') FROM eco_Repos")
	s += inquire('What is the average days since a eco_Repository was updated',
		"SELECT AVG(DATEDIFF(CURRENT_DATE, updated_at)) FROM eco_Repos")
	
	s += '\n'
	s += inquire('How many packages are available for this distribution?',
		"SELECT COUNT(*) FROM eco_Packages")
	s += inquire('How many of those packages have a BSD license?',
		"SELECT COUNT(DISTINCT eco_PkgLicenses.pkg_id) FROM eco_PkgLicenses, eco_Licenses WHERE lic_id = eco_Licenses.id AND eco_Licenses.name = 'BSD'")
	s += inquire('How many of the available packages are metapackages?',
		"SELECT COUNT(*) FROM eco_Packages WHERE isMetapackage = 1")
	s += inquire('Which packages is most commonly listed as a run dependency?',
		"SELECT eco_Packages.name, eco_PkgDeps.dep_id, COUNT(*) FROM eco_PkgDeps, eco_Packages WHERE eco_Packages.id = eco_PkgDeps.dep_id AND eco_PkgDeps.type_id = 3 GROUP BY dep_id ORDER BY COUNT(*) DESC LIMIT 1")
	
	s += '\n'
	s += inquire('How many authors are there?',
		"SELECT COUNT(DISTINCT ppl_id) FROM eco_PkgAuthors")
	s += inquire('How many maintainers are there?',
		"SELECT COUNT(DISTINCT ppl_id) FROM eco_PkgMntnrs")
	s += inquire('How many packages are there per maintainer?',
		"SELECT COUNT(DISTINCT eco_Packages.id)/COUNT(DISTINCT eco_PkgMntnrs.ppl_id) FROM eco_Packages, eco_PkgMntnrs")
	s += inquire('What is the average number of authors listed for a package?',
		"SELECT (SELECT COUNT(*) FROM eco_PkgAuthors) / (SELECT COUNT(*) FROM eco_Packages)")
	s += inquire('What is the average number of maintainers listed for a package?',
		"SELECT (SELECT COUNT(*) FROM eco_PkgMntnrs) / (SELECT COUNT(*) FROM eco_Packages)")

	s += '\n'
	s += inquire('Which package has the lowest health with a decent amount of impact?',
		"SELECT eco_Packages.name FROM eco_Packages, eco_PkgImpact, eco_PkgRepoHealth WHERE eco_PkgImpact.impact > 0.35 AND eco_Packages.id = eco_PkgRepoHealth.pkg_id ORDER BY eco_PkgRepoHealth.health DESC LIMIT 1")

	return s.replace('\n','',1)

def writeString(string):
	f = open('inquiries.txt','w')
	f.write(string)
	f.close()

if __name__ == '__main__':
	writeString(buildString())