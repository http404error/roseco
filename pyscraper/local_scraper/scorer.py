#!/usr/bin/env python

from people import Person, PersonSet
import package as pk

from operator import itemgetter

import yaml
import db_control

# Package Scoring

def scorePackages(packages):
	config_file = open('pkg_config.yaml', 'r')
	config = yaml.load(config_file)
	config_file.close()

	# Go through our impact metric settings and passs them on to their functions
	for metric_config in config:
		for elem in config[metric_config]:
			# Do not go through metric configurations unless we are including it
			if elem['include'] == True:
				
				if metric_config == 'impact':
					if elem['metric'] == 'direct_only':
						packages = scorePackageImpactDD(packages, elem['weight'])
					elif elem['metric'] == 'direct_indirect_discounted':
						packages = scorePackageImpactIDD(packages, elem['weights'])
				
				elif metric_config == 'health':
					if elem['metric'] == 'maintainer_num':
						packages = scorePackageHealthNumMaintainers(packages, elem['weight'])
					elif elem['metric'] == 'maintainer_email':
						packages = scorePackageHealthMaintainerEmails(packages, elem['weights'])
					elif elem['metric'] == 'github_issues':
						packages = scorePackageHealthGitHubIssues(packages, elem['weights'])

	packages = normalizeScores(packages, True)

	return packages

# IMPACT:
# Scores a dictionary of package objects on simply how many packages depend directly on it
def scorePackageImpactDD(packages, weight):
	for p in packages.values():
		all_depended = set()
		all_depended |= p.buildtool_depended
		all_depended |= p.build_depended
		all_depended |= p.run_depended
		p.impact = len(all_depended) * weight
	
	return packages

# Scores on how many packages depend directly and indirectly on it, all treated as equal
def scorePackageImpactID(packages):
	for p in packages.values():
		all_depended = set()
		all_depended |= p.closed_buildtool_depended
		all_depended |= p.closed_build_depended
		all_depended |= p.closed_run_depended
		p.impact = len(all_depended)
	
	return packages

# Scores on how many packages depend directly on it and discounts indirect dependencies
# Uses the depended degrees list of sets, which only has run dependencies
def scorePackageImpactIDD(packages, weights):
	for package in packages.values():
		impact = 0.0
		discount = weights['discount']

		weight = weights['buildtool_weight']
		for depset in package.buildtool_dep_orders:
			impact += len(depset) * weight
			weight = weight * discount
			package.buildtool_dep_orders_list.append(len(depset))

		weight = weights['build_weight']
		for depset in package.build_dep_orders:
			impact += len(depset) * weight
			weight = weight * discount
			package.build_dep_orders_list.append(len(depset))

		weight = weights['run_weight']
		for depset in package.run_dep_orders:
			impact += len(depset) * weight
			weight = weight * discount
			package.run_dep_orders_list.append(len(depset))

		package.impact = impact
	
	return packages

# HEALTH:
# Health based on number of maintainers
def scorePackageHealthNumMaintainers(packages, weight):
	for package in packages.values():
		package.health += float(len(package.maintainers)) * weight

	return packages

# Health based on the email type of the maintainers
def scorePackageHealthMaintainerEmails(packages, weights):
	for package in packages.values():
		for person in package.maintainers.people:
			for email in person.emails:
				for key in weights: # keys can be domain or extension
					if key in email:
						package.health += weights[key] # find the weight for that key

	return packages


def scorePackageHealthGitHubIssues(packages, weights):
	package_issue_counts = db_control.retrieveTableData(db = 'rosdb', table = 'package_health', 
		                                                cols = ['name', 'git_issues'], 
		                                                with_col_name = False, 
		                                                order_by = 'name', desc = False)
	
	score_list = [] # keep track of the score every package gets from this
	skipped_pkgs = []
	
	for package_issue_count in package_issue_counts:
		name = package_issue_count[0]
		issue_counts = package_issue_count[1]

		#store in git issues, temporary use, see packages.py
		packages[name].git_issues = package_issue_count[1]

		if 'noGit' in issue_counts or issue_counts == 'searchFailed':
			skipped_pkgs.append(packages[name])
		else:
			issue_count_list = issue_counts.split(',')
			starting_health = packages[name].health # used to keep track of how much was added from this
			
			for issue_count in issue_count_list:
				issue_count = issue_count.split(':')
				packages[name].health += int(issue_count[1]) * weights.get(issue_count[0].lower(), 0.0)
			
			score_list.append(packages[name].health - starting_health)

	# give packages without github issue records the average end score of those that do
	for skipped_pkg in skipped_pkgs:
		skipped_pkg.health += sum(score_list)/len(score_list)

	return packages



# Normalize the health and impact scores (separately) of the 
# packages by scaling between 0 and 1         
def normalizeScores(packages, equal_step = True):
	pkg_scores = []

	for package in packages.values():
		 pkg_scores.append([package.name,package.impact,package.health])
	
	if equal_step == False:
		max_scores = [max(pkg_scores, key=itemgetter(1))[1], max(pkg_scores, key=itemgetter(2))[2]]
		min_scores = [min(pkg_scores, key=itemgetter(1))[1], min(pkg_scores, key=itemgetter(2))[2]]

		for pkg_score in pkg_scores:
			for i in range(len(pkg_score[1:])):
				pkg_score[i+1] = (pkg_score[i+1] - min_scores[i])/(max_scores[i] - min_scores[i])
	
	else:
		impacts = []
		healths = []
		for pkg_score in pkg_scores:
			impacts.append(pkg_score[1])
			healths.append(pkg_score[2])
		unique_impacts = set(impacts)
		unique_healths = set(healths)


		for i in range(len(pkg_scores[0][1:])):
			
			all_scores = []
			for pkg_score in pkg_scores:
				all_scores.append(pkg_score[i+1])
			unique_scores = set(all_scores)

			step = 1.0/(len(unique_scores)-1)
			pkg_scores.sort(key=lambda x: x[i+1])
			start = 0.0

			for pkg_score in pkg_scores:
				try:
					unique_scores.remove(pkg_score[i+1])
					pkg_score[i+1] = start
					start += step
				except:
					pkg_score[i+1] = start
	
	for pkg_score in pkg_scores:
		packages[pkg_score[0]].impact = pkg_score[1]
		packages[pkg_score[0]].health = pkg_score[2]

	return packages

# People Scoring

def scorePeople(packages):
	config_file = open('ppl_config.yaml', 'r')
	config = yaml.load(config_file)
	config_file.close()

	mntnrs = reduce(set.union, [p.maintainers.people for p in packages.values()])
	authors = reduce(set.union, [p.authors.people for p in packages.values()])
	people = mntnrs.union(authors)
	
	config = config['impact']
	
	for person in people:
		for package in packages.values():
			if config[0]['include'] == True:
				if package.maintainers.find(person) != None:
					# Person's impact score is affected by both the number of 
					# packages they maintain and how impactful these packages are
					person.impact += package.impact * config[0]['weight']
					person.pkgs_maintaining += 1
			if config[1]['include'] == True:
				if package.authors.find(person) != None:
					# Person's impact score is affected by both the number of 
					# packages they authored and how impactful these packages are
					person.impact += package.impact * config[1]['weight']
					person.pkgs_authored += 1

	people = normalizePeopleScores(people)
	return people

def normalizePeopleScores(people):
	scores = []
	for person in people:
		scores.append(person.impact)
	for person in people:
		person.impact = (person.impact - min(scores))/(max(scores) - min(scores))
	return people

if __name__ == '__main__':
	packages = pk.makePackageList('/opt/ros/hydro/share')
	packages = scorePackages(packages)
	people = scorePeople(packages)
	# print len(people)
	# for p in people:
	# 	print p.name, p.impact