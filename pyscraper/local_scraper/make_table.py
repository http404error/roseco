#!/usr/bin/python

import package as pk 
import scorer as sc
import db_control

def makeTable(data):
	s = '<table>\n'
	for i in range(len(data)):
		s += '<tr>\n'
		if i == 0:
			s += '\t<th>' + '</th>\n\t<th>'.join(data[i]) + '</th>'
		else:
			s += '\t<td>' + '</td>\n\t<td>'.join(map(str,data[i])) + '</td>'
		s += '\n</tr>\n'
	s += '</table>'
	return s

if __name__ == '__main__':
	package_impact = db_control.retrieveTableData(db = 'rosdb', table = 'package_impact', 
	                                              cols = 'all', with_col_name = True, 
	                                              order_by = 'impact')
	package_health = db_control.retrieveTableData(db = 'rosdb', table = 'package_health', 
	                                              cols = 'all', with_col_name = True, 
	                                              order_by = 'health')
	people_impact =  db_control.retrieveTableData(db = 'rosdb', table = 'people_impact', 
	                                              cols = 'all', with_col_name = True, 
	                                              order_by = 'impact')

	s = makeTable(package_impact)
	s += makeTable(package_health)
	s += makeTable(people_impact)

	f = open('table.html', 'w')
	f.write(s)