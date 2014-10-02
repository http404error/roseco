import db_control as dbc
import db_extract as dbe

from datetime import date, datetime
import time

# helpful global type variables
S6 = 'SMALLINT(6)'
M9 = 'MEDIUMINT(9)'
V20 = 'VARCHAR(50)'

# Used to record meta data on the main tables, methods to perform various
# db.extract functions, apendthing the data to be recorded after method calls
class Historian:
	def __init__(self, con, cur, name, cols, types, table, table2 = None):
		self.con = con
		self.cur = cur

		self.name = name

		assert len(cols) == len(types)
		self.cols = cols
		self.types = types

		self.table = table
		self.table2 = table2

		self.row = []

	def apndCount(self):
		self.row.append(dbe.getTable(
			self.cur, self.table, ['*'], cnt = True))

	def apndMatchCount(self, mcol, val):
		self.row.append(dbe.getMatch(
			self.cur, self.table, ['*'], mcol, val, cnt = True))

	def apndLikeCount(self, lcol, val):
		self.row.append(dbe.getLike(
			self.cur, self.table, ['*'], lcol, val, cnt = True))

	def apndDistinctCount(self, col):
		self.row.append(dbe.getDistinct(
			self.cur, self.table, [col], cnt = True))

	def apnd2MatchCount(self, mcol1, mcol2, val1, val2):
		self.row.append(dbe.get2Match(
			self.cur, self.table, mcol1, mcol2, val1, val2, cnt = True))

	def apndColSum(self, col):
		self.row.append(dbe.getTable(
			self.cur, self.table, [col], sums = True))



	# last step of any historian
	def recordTable(self):
		try:
			assert len(self.row) == len(self.cols)
		except:
			print self.name, self.cols
			print self.row, '\n'

		# All chronicler tables record the date of each row
		self.cols.append('date')
		self.types.append('VARCHAR(10)')
		self.row.append(time.strftime("%Y-%m-%d"))
		data = [tuple(self.row)]
		dbc.recordTable(
			self.con, self.cur, self.name, self.cols, self.types, data)


	# specific functions
	def apndTotalDaysAgo(self, col, mcol, val):
		day_col = dbe.getMatch(self.cur, self.table, [col], mcol, val)

		def daysAgo(date_string):
			return (date.today() - datetime.strptime(date_string,'%Y-%m-%d').date()).days

		c = 0
		for date_str in day_col:
			c += daysAgo(date_str[0])
		self.row.append(c)

	def apndFreqVals(self, colcnt, col, mcol, top_num = None):
		mcom_ids = dbe.getMostCom(self.cur, self.table, colcnt, top_num)
		for mcom_id,mcom_cnt in mcom_ids:
			match = dbe.getMatchVal(self.cur, self.table2, [col], mcol, mcom_id)
			self.row.append(match)
			self.row.append(mcom_cnt)
		# In case there were not enough to mee the top_num count
		for i in range(top_num - len(mcom_ids)):
			self.row.append(None)
			self.row.append(None)

	def apndFreqValsCount(self, colcnt, thresh = None, thresh2 = None):
		mcom_ids = dbe.getMostCom(self.cur, self.table, colcnt, top_num = None)
		c = 0
		for mcom_id,mcom_cnt in mcom_ids:
			if thresh2 == None:
				if mcom_cnt >= thresh:
					c += 1
			else:
				if mcom_cnt >= thresh and mcom_cnt < thresh2:
					c += 1
		self.row.append(c)


def chronIssuesHist(con, cur):
	cols = ['open','closed','open_unassigned','days_open']
	types = [M9,M9,M9,M9]
	issuesHist = Historian(con, cur, 'Issues_Hist', cols, types, 'Issues')
	issuesHist.apndMatchCount('closed_at', 'NULL')
	issuesHist.apndMatchCount('closed_at', 'NOT NULL')
	issuesHist.apnd2MatchCount('assigned_to', 'closed_at', 'NULL', 'NULL')
	issuesHist.apndTotalDaysAgo('created_at', 'closed_at', 'NULL')
	issuesHist.recordTable()

def chronIssuesLabels(con, cur):
	cols = ['l1','l1_count','l2','l2_count','l3','l3_count']
	types = [V20,S6,V20,S6,V20,S6]
	labelHist = Historian(con, cur, 'Labels_Hist', cols, types, 
		'IssuesLabels', 'Labels')
	labelHist.apndFreqVals('label_id', 'name', 'id', top_num = 3)
	labelHist.recordTable()

def chronLicenses(con, cur):
	cols = ['l1','l1_count','l2','l2_count','l3','l3_count']
	types = [V20,S6,V20,S6,V20,S6]
	licHist = Historian(con, cur, 'Licenses_Hist', cols, types, 
		'PkgLicenses', 'Licenses')
	licHist.apndFreqVals('lic_id', 'name', 'id', top_num = 3)
	licHist.recordTable()

def chronPkgs(con, cur):
	cols = ['pkgs','metapkgs']
	types = [S6,S6]
	pkgHist = Historian(con, cur, 'Packages_Hist', cols, types, 'Packages')
	pkgHist.apndMatchCount('isMetapackage', 0)
	pkgHist.apndMatchCount('isMetapackage', 1)
	pkgHist.recordTable()

def chronPpl(con, cur):
	cols = ['ppl', 'edu_ppl','osrf_ppl', 'willow_ppl']
	types = [S6,S6,S6,S6]
	pplHist = Historian(con, cur, 'People_Hist', cols, types, 'People')
	pplHist.apndCount()
	pplHist.apndLikeCount('email', 'edu')
	pplHist.apndLikeCount('email', 'osrf')
	pplHist.apndLikeCount('email', 'willowgarage')
	pplHist.recordTable()

def chronPkgMntnrs(con, cur):
	cols = ['mntnrs','mntnr_links','pkgs_with_mntnr','pkgs_with_2plus']
	types = [S6,S6,S6,S6]
	mntnrHist = Historian(con, cur, 'PkgMntnrs_Hist',cols, types,'PkgMntnrs')
	mntnrHist.apndDistinctCount('ppl_id')
	mntnrHist.apndCount()
	mntnrHist.apndDistinctCount('pkg_id')
	mntnrHist.apndFreqValsCount('pkg_id', 2)
	mntnrHist.recordTable()

def chronPkgAuthors(con, cur):
	cols = ['auths','auths_links','pkgs_with_auth','pkgs_with_2plus']
	types = [S6,S6,S6,S6]
	authorHist = Historian(con, cur, 'PkgAuthors_Hist',cols, types,'PkgAuthors')
	authorHist.apndDistinctCount('ppl_id')
	authorHist.apndCount()
	authorHist.apndDistinctCount('pkg_id')
	authorHist.apndFreqValsCount('pkg_id', 2)
	authorHist.recordTable()

def chronPkgDeps(con, cur):
	cols = ['all_deps','builtool','build','run','p1','deps_onp1','p2','deps_onp2','p3','deps_onp3']
	types = [S6,S6,S6,S6,V20,S6,V20,S6,V20,S6]
	pkgDepHist = Historian(con, cur, 'PkgDeps_Hist',cols, types, 'PkgDeps', 'Packages')
	pkgDepHist.apndCount()
	pkgDepHist.apndMatchCount('type_id', 1)
	pkgDepHist.apndMatchCount('type_id', 2)
	pkgDepHist.apndMatchCount('type_id', 3)
	pkgDepHist.apndFreqVals('dep_id','name','id', top_num = 3)
	pkgDepHist.recordTable()

def chronGitPpl(con, cur):
	cols = ['gitppl']
	types = [S6]
	gitPplHist = Historian(con, cur, 'GitPpl_Hist', cols, types, 'GitPpl')
	gitPplHist.apndCount()
	gitPplHist.recordTable()

def chronGitUsers(con, cur):
	cols = ['users']
	types = [M9]
	gitUsersHist = Historian(con, cur, 'GitUsers_Hist', cols, types, 'GitUsers')
	gitUsersHist.apndCount()
	gitUsersHist.recordTable()

def chronRepos(con, cur):
	cols = ['repos', 'release_repos','orgs_repos','user_repos','days_unupdated','forks','watchers','subrs','total_size']
	types = [S6, S6, S6, S6, M9, M9, M9, M9, M9]
	reposHist = Historian(con, cur, 'Repos_Hist', cols, types, 'Repos')
	reposHist.apndCount()
	reposHist.apndLikeCount('name','release')
	reposHist.apndMatchCount('owner_type','Organization')
	reposHist.apndMatchCount('owner_type','User')
	reposHist.apndTotalDaysAgo('updated_at','created_at','NOT NULL')
	reposHist.apndColSum('forks_count')
	reposHist.apndColSum('watchers_count')
	reposHist.apndColSum('subscribers_count')
	reposHist.apndColSum('size')
	reposHist.recordTable()

def chronPkgRepos(con, cur):
	cols = ['pkgs_with_1repo', 'pkgs_with_2repos']
	types = [S6, S6]
	pkgReposHist = Historian(con, cur, 'PkgRepos_Hist', cols, types, 'PkgRepos')
	pkgReposHist.apndFreqValsCount('pkg_id', 1, 2)
	pkgReposHist.apndFreqValsCount('pkg_id', 2)
	pkgReposHist.recordTable()



def chronicle(con, cur):
	chronIssuesHist(con, cur)
	chronIssuesLabels(con, cur)
	chronLicenses(con, cur)
	chronPkgs(con, cur)
	chronPpl(con, cur)
	chronPkgMntnrs(con, cur)
	chronPkgAuthors(con, cur)
	chronPkgDeps(con, cur)
	chronGitPpl(con, cur)
	chronGitUsers(con, cur)
	chronRepos(con, cur)
	chronPkgRepos(con, cur)

if __name__ == '__main__':
	print "\nConnecting to database"
	con, cur = dbc.conCur()
	chronicle(con, cur)