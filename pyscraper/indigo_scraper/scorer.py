#!/usr/bin/env python

from people import Person, PersonSet
import package as pk

from operator import itemgetter
from datetime import date, datetime
import numpy as np

import yaml
import db_control as dbe
import db_extract as dbe

import sys
import os

# Returns health/impact list of tuples for table insertion

def getPkgsHealth(pkg_ids, cur):
	# Open config file and extract yaml
	with open(os.path.join('score_config','pkg_health.yaml'),'r') as config_file:
		config = yaml.load(config_file)

	pkg_health = scorePkgsHealth(pkg_ids, config['health'], cur)
	
	return pkg_health

def getPkgsImpact(pkg_ids, cur):
	with open(os.path.join('score_config','pkg_impact.yaml'),'r') as config_file:
		config = yaml.load(config_file)

	pkg_impact = scorePkgsImpact(pkg_ids, config['impact'], cur)
	
	return pkg_impact

def getReposHealth(repo_ids, cur):
	with open(os.path.join('score_config','repo_health.yaml'),'r') as config_file:
		config = yaml.load(config_file)

	repo_health = scoreReposHealth(repo_ids, config['health'], cur)
	
	return repo_health

def getPplImpact(ppl_ids, cur):
	with open(os.path.join('score_config','ppl_impact.yaml'),'r') as config_file:
		config = yaml.load(config_file)

	ppl_impact = scorePplImpact(ppl_ids, config['impact'], cur)

	return ppl_impact

def getPkgsReposHealth(pkg_ids, repo_ids, cur):
	with open(os.path.join('score_config','pkg_repo_health.yaml'),'r') as config_file:
		config = yaml.load(config_file)

	pkg_repo_health = scorePkgsReposHealth(pkg_ids, repo_ids, config['health'], cur)

	return pkg_repo_health

# Composite health/impact metric scorers

def scorePkgsHealth(pkg_ids, health_config, cur):
	# Initialize health scores with all zeros to pass to functions, keep as list to update scores
	health_scores = []
	for pkg_id in pkg_ids:
		health_scores.append([pkg_id[0], 0.0 ])

	for metric_config in health_config:
		include = metric_config['include']
		weights = metric_config['weights']
		if metric_config['metric'] == 'maintainer_num' and include:
			health_scores = scorePkgsMntnrNum(health_scores, weights, cur)
		if metric_config['metric'] == 'maintainer_email' and include:
			health_scores = scorePkgsMntnrEmail(health_scores, weights, cur)

	return makeNormalizedLot(health_scores)

def scorePkgsImpact(pkg_ids, impact_config, cur):
	impact_scores = []
	for pkg_id in pkg_ids:
		impact_scores.append([pkg_id[0], 0.0])
	# With more than one impact score this will need to be init'd with zeros

	for metric_config in impact_config:
		include = metric_config['include']
		weights = metric_config['weights']
		if metric_config['metric'] == 'discounted_depended_orders' and include:
			impact_scores = scorePkgsDDO(impact_scores, weights, cur)
	
	return makeNormalizedLot(impact_scores)

def scoreReposHealth(repo_ids, health_config, cur):
	health_scores = []
	for repo_id in repo_ids:
		health_scores.append([repo_id[0], 0.0 ])

	for metric_config in health_config:
		include = metric_config['include']
		weights = metric_config['weights']
		if metric_config['metric'] == 'github_repos' and include:
			health_scores = scoreReposInfo(health_scores, weights, cur)
		if metric_config['metric'] == 'github_issues' and include:
			health_scores = scoreReposIssues(health_scores, weights, cur)

	return makeNormalizedLot(health_scores)

def scorePplImpact(ppl_ids, impact_config, cur):
	impact_scores = []
	for ppl_id in ppl_ids:
		impact_scores.append([ppl_id[0], 0.0 ])

	for metric_config in impact_config:
		include = metric_config['include']
		weights = metric_config['weights']
		if metric_config['metric'] == 'pkg_num':
			impact_scores = scorePplPkgNum(impact_scores, weights, cur)
		if metric_config['metric'] == 'pkg_impact':
			impact_scores = scorePplPkgImpact(impact_scores, weights, cur)

	return makeNormalizedLot(impact_scores)

def scorePkgsReposHealth(pkg_ids, repo_ids, health_config, cur):
	health_scores = []
	for pkg_id in pkg_ids:
		health_scores.append([pkg_id[0], 0.0 ])

	for metric_config in health_config:
		include = metric_config['include']
		weights = metric_config['weights']
		if metric_config['metric'] == 'pkg_repo_health_composite' and include:
			health_scores = scorePkgsReposHealthComp(health_scores, weights, cur)

	return makeNormalizedLot(health_scores)


# Health metrics:
def scorePkgsMntnrNum(health_scores, weights, cur):
	weight = weights['weight']
	for score in health_scores:
		pkg_id = score[0]
		mntnr_num = dbe.getMatch(cur,table='PkgMntnrs',cols=['ppl_id'],match_col='pkg_id',val=pkg_id,num=True)
		score[1] += mntnr_num * weight
	return health_scores

def scorePkgsMntnrEmail(health_scores, weights, cur):
	for score in health_scores:
		pkg_id = score[0]
		pkg_mntnrs = dbe.getMatch(cur,table='PkgMntnrs',cols=['ppl_id'],match_col='pkg_id',val=pkg_id)
		for pkg_mntnr in pkg_mntnrs:
			emails = dbe.getMatch(cur,table='People',cols=['emails'],match_col='id',val=pkg_mntnr[0])[0] # Index bc a nested tuple
			for email in emails:
				if email == None:
					continue
				for key in weights:
					if key in email:
						score[1] += weights[key]
	return health_scores

def scoreReposInfo(health_scores, weights, cur):
	for score in health_scores:
		repo_id = score[0]
		cols = ['owner_type','created_at','updated_at','pushed_at','size',
		        'forks_count','watchers_count','subscribers_count']
		repo_info = dbe.getMatch(cur,table='Repos',cols=cols,match_col='id',val=repo_id)[0] # Know there's only 1 row per repo id
		# Repo_info returns the info in the same order as the cols provided
		for idx,col in enumerate(cols):
			if col in ['created_at','updated_at','pushed_at']: # Those with dates
				days_ago = daysAgo(repo_info[idx])
				score[1] += days_ago * weights[col]
			elif col == 'owner_type':
				for owner_type in weights[col]:
					if owner_type == repo_info[idx].lower():
						score[1] += weights[col][owner_type]
			else:
				score[1] += repo_info[idx] * weights[col]

	return health_scores

def scoreReposIssues(health_scores, weights, cur):
	label_names = dbe.getTable(cur, table='Labels', cols=['id','name'])
	for score in health_scores:
		repo_id = score[0]
		# closed at is first column to determine if other weights are applied
		cols = ['id','closed_at','assigned_to','created_at']
		issues_info = dbe.getMatch(cur,table='Issues',cols=cols,match_col='repo_id',val=repo_id)
		for issue in issues_info:
			closed = False
			for idx,col in enumerate(cols):
				if col == 'closed_at' and issue[idx] != None:
					score[1] += weights[col]
					closed = True
					break
				elif col == 'created_at':
					days_ago = daysAgo(issue[idx])
					score[1] += days_ago * weights[col]
				elif col == 'assigned_to' and issue[idx] != None:
					score[1] +=  weights[col]

			if closed == False:
				# Label weights for score only used if open
				issue_id = issue[0]
				label_ids = dbe.getMatch(cur,table='IssuesLabels',cols=['label_id'],match_col='issue_id',val=issue_id)
				for label_id in label_ids:
					name = label_names[label_id[0]-1][1]
					for label_weight_name in weights['labels']:
						if label_weight_name == name:
							score[1] += weights['labels'][label_weight_name]

	return health_scores

def scorePkgsReposHealthComp(health_scores, weights, cur):
	pkg_health_weight = weights['pkg_health_weight']
	repo_health_weight = weights['repo_health_weight']
	for score in health_scores:
		pkg_id = score[0]
		pkg_health = dbe.getMatch(cur,table='PkgHealth',cols=['health'],match_col='pkg_id',val=pkg_id)[0][0]
		repo_ids = dbe.getMatch(cur,table='PkgRepos',cols=['repo_id'],match_col='pkg_id',val=pkg_id)
		if repo_ids != None:
			# Pkgs can be linked to more than one (release or source) repo
			score[1] += pkg_health * pkg_health_weight
			for repo_id in repo_ids:
				repo_health = dbe.getMatch(cur,table='RepoHealth',cols=['health'],match_col='repo_id',val=repo_id[0])[0][0]
				score[1] += repo_health * repo_health_weight
		else:
			print "Package (id:", health_score[0], ") without Repo"
			score = None

	return health_scores



# Impact metrics:
def scorePkgsDDO(impact_scores, weights, cur):
	# DDO = Discounted Dependency Orders
	# Scores all packages based on discounted orders of dependency
	weight = weights['weight']
	discount = weights['discount']

	def scoreDiscDepOrders(weight, discount, depended_orders_num):
		score = 0.0
		for dep_order_num in depended_orders_num:
			score += dep_order_num * weight
			weight = weight * discount
		return score

	for score in impact_scores:
		pkg_id = score[0]
		depended_orders_num = dbe.getDepOrders(cur, pkg_id)
		print depended_orders_num, '\t', 
		score[1] += scoreDiscDepOrders(weight, discount, depended_orders_num)
	print
	return impact_scores

def scorePplPkgNum(impact_scores, weights, cur):
	# Number of packages authored or maintaining
	# Weighted based on relationship (authored or maintaining)
	for score in impact_scores:
		ppl_id = score[0]
		mntning_num = dbe.getMatch(cur,table='PkgMntnrs',cols=['pkg_id'],match_col='ppl_id',val=ppl_id,num=True)
		authored_num = dbe.getMatch(cur,table='PkgAuthors',cols=['pkg_id'],match_col='ppl_id',val=ppl_id,num=True)
		score[1] += mntning_num * weights['maintaining']
		score[1] += authored_num * weights['authored']

	return impact_scores

def scorePplPkgImpact(impact_scores, weights, cur):
	# The impact of package(s) associated with this person, weighted on relationship
	for score in impact_scores:
		ppl_id = score[0]
		
		pkgs_mntning = dbe.getMatch(cur,table='PkgMntnrs',cols=['pkg_id'],match_col='ppl_id',val=ppl_id)
		if len(pkgs_mntning) != 0:
			for pkg_mntning in pkgs_mntning:
				pkg_id = pkg_mntning[0]
				pkg_impact = dbe.getMatch(cur,table='PkgImpact',cols=['impact'],match_col='pkg_id',val=pkg_id)[0][0]
				score[1] += pkg_impact * weights['maintaining']
		
		pkgs_authored = dbe.getMatch(cur,table='PkgAuthors',cols=['pkg_id'],match_col='ppl_id',val=ppl_id)
		if len(pkgs_authored) != 0:
			for pkg_authored in pkgs_authored:
				pkg_id = pkg_authored[0]
				pkg_impact = dbe.getMatch(cur,table='PkgImpact',cols=['impact'],match_col='pkg_id',val=pkg_id)[0][0]
				score[1] += pkg_impact * weights['authored']

	return impact_scores

# Metric Helpers:
def daysAgo(date_string):
	return (date.today() - datetime.strptime(date_string,'%Y-%m-%d').date()).days

def makeNormalizedLot(lol):
	max_score = max(lol, key=itemgetter(1))[1]
	min_score = min(lol, key=itemgetter(1))[1]
	range_score = max_score - min_score
	if range_score == 0: div_zero = True
	else: div_zero = False

	lot = []
	for l in lol:
		if div_zero:
			lot.append(tuple(( l[0], 0.0 )))
		else:	
			n_score = (l[1] - min_score) / range_score
			lot.append(tuple(( l[0], n_score )))
	return lot

# Function to exclude outer most std dev before normalizing
def makeNormLotRejectOutliers(lol, m=2.0):
	s_only = np.array([l[1] for l in lol]) # Make a numpy array of only the scores
	s_mean = np.mean(s_only)
	s_stdev = np.std(s_only)
	if s_stdev == 0: div_zero = True
	else: z_scores = (s_only - s_mean) / s_stdev
	
	max_s = max(s_only)
	min_s = min(s_only)
	range_s = max_s - min_s
	if range_s == 0: div_zero = True
	else: div_zero = False

	lot = []
	o_c = 0
	z_c = 0
	c = 0
	for idx,l in enumerate(lol):
		if div_zero:
			lot.append(tuple(( l[0], 0.0 )))
		else:
			n_s = (l[1] - min_s) / range_s
			if z_scores[idx] > m:
				lot.append(tuple(( l[0], 1.0 )))
				o_c += 1
			elif z_scores[idx] < -m:
				lot.append(tuple(( l[0], 0.0 )))
				z_c += 1
			else:
				lot.append(tuple(( l[0], n_s )))
				c += 1

	print "Total: ", len(lot), "Non-outliers: ", c, "\tOutliers: upper;", o_c, " lower;", z_c

	return lot
		

if __name__ == '__main__':
	# packages = pk.makePackageDict('./manifests')
	con, cur = dbc.conCur(user='dbuser',passwd='dbpass',db='test2',host='localhost',port=None)

	# pkg_ids = [(1, 'monocam_settler'), (2, 'xacro'), (4,'bond_core')]
	# # ppl_ids = [(4, 'Stu Glaser'),(14, 'William Woodall')]
	# pkg_impact, pkg_health = scorePkgs(packages, pkg_ids, cur)
	# print pkg_impact, pkg_health

	# pkg_only_ids = [(1),(2)]
	# repo_only_ids = [(1),(2)]
	# pkg_repo_health = getPkgsReposHealth(pkg_only_ids, repo_only_ids, cur)

	health_scores = [[0,200],[1, -797.5699999999997], [2, -126.16500000000006], [3, -20.849999999999994], [4, -97.94000000000001], [5, -193.83499999999998], [6, -3714.824999999995], [7, -60.94500000000005], [8, -224.29499999999982], [9, -1457.5050000000099], [10, -67.89000000000031]]
	# makeNormalizedLot(health_scores)
	print makeNormLotRejectOutliers(health_scores)