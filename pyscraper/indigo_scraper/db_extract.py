import db_control as dbc

# Helper retriever
def exFetch(cur,cmd):
	cur.execute(cmd)
	return cur.fetchall()

def getTable(cur, table, cols, row_max=None):
	table = '`' + table + '`'
	cmd = 'SELECT '
	for col in cols:
		cmd += col + ', '
	cmd = cmd[:-2] + ' FROM %s ' % table
	if row_max != None: cmd += 'WHERE id <= ' + str(row_max) + ' '
	cmd += 'ORDER BY id ASC'
	result = list(exFetch(cur,cmd))
	return result

def getMatch(cur, table, cols, match_col, val, num=False):
	table = '`' + table + '`'
	cmd = 'SELECT '
	for col in cols:
		cmd += col + ', '
	cmd = cmd[:-2] + ' FROM '+table+' WHERE '+match_col+' = '
	if type(val) == type(5): cmd += str(val)
	elif type(val) == type('string'): cmd += "'" + val + "'"
	elif type(val) == type(('tup','le')): cmd += str(val[0])

	
	result = exFetch(cur,cmd)

	if num == True:
		return len(result)
	else:
		return result

def getMatchFromMatch(cur,table,table2,match_col,match_col2,val,val2):
	result = getMatch(cur, table, cols, match_col, val)
	print result

def getMatchSet(cur, table, cols, match_col, val):
	s = set()
	tot = getMatch(cur, table, cols, match_col, val)
	for t in tot:
		if len(t) == 1: s.add(t[0])
		else: s.add(t)
	return s

def getSingleMatch(cur,table,cols,match_col,val,num=False):
	result = getMatch(cur, table, cols, match_col, val, num)
	assert len(result) == 1
	return result[0]

def getSingleVal(cur,table,col,match_col,val):
	# use for: name,  isMeta, description, impact, health
	if type(col) != type(['list']): col = [col]
	result = getSingleMatch(cur,table,col,match_col,val)
	return result[0]

def getSingleValFromSet(cur,table,col,match_col,val_set):
	ret_set = set()
	for val in val_set:
		ret_set.add(getSingleVal(cur, table, col, match_col, val))
	return ret_set

# Used for finding dependency number orders
def getDepOrders(cur, dep_id):
	# Used for impact scoring
	dep_orders = []
	cmd = 'SELECT DISTINCT pkg_id FROM PkgDeps WHERE dep_id = ' + str(dep_id)
	result = exFetch(cur, cmd)

	def addOrder(dep_orders, result):
		this_dep_order = set()
		for dep_id in result:
			if not any(dep_id in dep_order for dep_order in dep_orders):
				this_dep_order.add(dep_id[0])
		dep_orders.append(this_dep_order)
		return dep_orders

	# Seed with direct dependencies
	dep_orders = addOrder(dep_orders, result)

	while_count = 0
	while while_count < 10:
		if while_count == 0:
			cmd = cmd.replace('=','!=') + ' AND dep_id IN (' + cmd + ')'
		else:
			cmd = cmd.replace(' AND dep_id IN ', ' AND dep_id NOT IN ') + ' AND dep_id IN (' + cmd + ')'
		result = exFetch(cur, cmd)
		if len(result) == 0:
			break
		dep_orders = addOrder(dep_orders, result)
		while_count += 1

	# Only return the number of dependency for each order
	dep_order_nums = []
	if len(dep_orders) == 0:
		dep_order_nums.append(0)
	else:
		for dep_order in dep_orders:
			dep_order_nums.append(len(dep_order))
	return dep_order_nums
	

if __name__ == '__main__':
	# con, cur = concur(user='smartroswiki', passwd='p0tyYjIr', db='smartroswiki', host='engr-db.engr.oregonstate.edu', port=3307)
	con, cur = dbc.conCur()
	# print getVal(cur,'PkgHealth','health','pkg_id',4)

	# lot = getMatchSet(cur,'PkgDeps',['dep_id'],'pkg_id',1)
	# pkg_info = getSingleMatch(cur,'Packages',['name','isMetapackage','description'],'id',9)
	
	dep_ids = getMatchSet(cur, 'PkgDeps',['dep_id','type_id'],'pkg_id', 9)
	print dep_ids
	run_dep_id = getSingleVal(cur,'PkgDepTypes',['id'],'dep_type','run_depend')
	print getSingleValFromSet(cur, 'Packages',['name'],'id',dep_ids)
	run_deps = set(d[0] for d in dep_ids if d[1] == run_dep_id)
	print run_deps
	print getSingleValFromSet(cur, 'Packages',['name'],'id',run_deps)
	exit()

	print getTable(cur, 'Packages',['id'],9)
	print getSingleVal(cur, 'Packages',['isMetapackage'],'id',9)
	print getMatch(cur, 'PkgDeps',['dep_id','type_id'],'pkg_id', 9)
	print getSingleVal(cur, 'PkgDepTypes',['id'],'dep_type','run_depend')
	print getSingleVal(cur, 'Packages',['description'], 'id',9)
	print getSingleVal(cur, 'Packages',['name'],'id',9)
	print getSingleVal(cur, 'Packages',['name'],'id',9)
	print getSingleVal(cur, 'PkgImpact','impact','pkg_id',9)
	print getSingleVal(cur,'PkgRepoHealth','health','pkg_id',9)
	match_set = getMatchSet(cur,'PkgAuthors',['ppl_id'],'pkg_id', 9)
	print getSingleValFromSet(cur, 'People', 'name', 'id', match_set)
	match_set = getMatchSet(cur, 'PkgDeps',['dep_id'],'pkg_id',9)
	print getSingleValFromSet(cur, 'Packages',['name'],'id',match_set)

	