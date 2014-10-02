import db_extract as dbe 
import db_control as dbc 

con, cur = dbc.conCur(db='ROSdb')

# cmd = 'SELECT eco_People.name, COUNT(*) FROM eco_People, eco_PkgMntnrs WHERE eco_People.id = eco_PkgMntnrs.ppl_id GROUP BY eco_PkgMntnrs.ppl_id ORDER BY COUNT(*) DESC LIMIT 50;'
# answer = dbe.exFetch(cur, cmd)

# for p in answer:
# 	print p[0] + ', ' + str(p[1])

cmd = 'SELECT name FROM eco_Repos WHERE DATEDIFF(CURRENT_DATE, updated_at) > 182'
answer = dbe.exFetch(cur, cmd)
for p in answer:
	print p[0]

print 'year\n\n'

cmd = 'SELECT name FROM eco_Repos WHERE DATEDIFF(CURRENT_DATE, updated_at) > 364'
answer = dbe.exFetch(cur, cmd)
for p in answer:
	print p[0]