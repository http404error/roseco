import numpy as np
import matplotlib.pyplot as plt

import db_control as dbc
import db_extract as dbe

import sys

def pltImpHealth(cur):
	imps = dbe.getTable(cur, 'Repos', ['subscribers_count'])
	imps = np.ndarray.flatten(np.asarray(imps))

	hels = dbe.getTable(cur, 'Repos', ['size'])
	hels = np.ndarray.flatten(np.asarray(hels))

	# area = np.pi * (15 * np.random.rand(N))**2 # 0 to 15 point radiuses

	# plt.scatter(x, y, s=area, alpha=0.5)
	plt.scatter(imps, hels, alpha = 0.5)
	plt.show()

if __name__ == '__main__':
	con, cur = dbc.conCur()
	pltImpHealth(cur)