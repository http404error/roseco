#!/usr/bin/env python

# from people import Person, PersonSet
from package import *
from operator import itemgetter

def networkifyPackages(packages):
    s = ''
    counter = 1
    s += '*Vertices ' + str(len(packages)) + '\n'
    for p in packages:
        p.pajek_num = counter
        s += str(p.pajek_num) + ' ' + p.name + '\n'
        counter += 1
    s += '*Arcslist\n'
    for p in packages:
        s += str(p.pajek_num)
        arcs = p.getAllDepend()
        for a in arcs:
            for q in packages:
                if (q.name == a):
                    s += ' ' + str(q.pajek_num)
        s += '\n'
    return s


packages = makePackageList('/opt/ros/hydro/share')
f = open('ros.net', 'w')
f.write(networkifyPackages(packages.values()).encode('ascii', 'xmlcharrefreplace'))
f.close()
print('package data written to ros.net')
