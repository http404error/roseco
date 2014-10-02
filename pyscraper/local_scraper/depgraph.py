#!/usr/bin/env python

from people import Person, PersonSet
from package import *

import sys
import pygraphviz as pgv

# Colormap dictionary for coloring based on dependency type
colormap = {'buildtool':'green', 'build':'blue', 'run':'red'}

if __name__ == '__main__':
    packages = makePackageList('/opt/ros/hydro/share')

    graph = pgv.AGraph(strict=False, directed=True)

    for name, package in packages.iteritems():
        no_deps = True
        for deptype in deptypes:
            for dep in package.depend[deptype]:
                no_deps = False
                graph.add_edge(dep, name)#, color=colormap[deptype])
        if no_deps == True:
            graph.add_node(name)

    graph.tred()

    graph.layout(prog='dot')

    graph.draw('graph.png')
    print 'graph written to file'
