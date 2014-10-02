#!/usr/bin/env python

from people import Person, PersonSet
from package import *
from operator import itemgetter
import scorer

# Takes a string
def jsonifyItem(i):
    return '\t\t\t\t\"' + i + '\"'

# Takes an iterator (over an iterable of strings)
def jsonifyMultiItem(it):
    s = ''
    try:
        s += jsonifyItem(next(it))
        for string in it:
            s += ',\n' + jsonifyItem(string)
        s += '\n'
    except StopIteration:
        pass
    return s;

# Takes a package object
def jsonifyPackage(p):
    s = ''
    s += '\t\t{\n'
    s += '\t\t\t\"Name\": \"' + p.name + '\",\n'
    s += '\t\t\t\"Metapackage\": ' + ('true' if p.isMetapackage else 'false') + ',\n'
    if (p.isMetapackage):
        s += '\t\t\t\"Contains\": [\n' # Only used for metapackages
        s += jsonifyMultiItem(iter(p.run_depend))
        s += '\t\t\t],\n'
    s += '\t\t\t\"Description\": \"' + p.description + '\",\n'

    s += '\t\t\t\"Quality\": ' + str(p.quality) + ',\n'
    s += '\t\t\t\"Impact\": ' + str(p.impact) + ',\n'
    s += '\t\t\t\"Health\": ' + str(p.health) + ',\n'
    s += '\t\t\t\"Runtime\": ' + str(p.runtime) + ',\n'

    s += '\t\t\t\"Authors\": [\n'
    authorstrings = set()
    for person in p.authors.people:
        authorstrings.add(person.name)
    s += jsonifyMultiItem(iter(authorstrings))
    s += '\t\t\t],\n'
    s += '\t\t\t\"Edge\": [\n'
    s += jsonifyMultiItem(iter(p.getAllDepend()))
    s += '\t\t\t]\n'
    s += '\t\t}'
    return s

def jsonifyPackages(packages):
    s = ''
    s +='[{\n'
    s += '\t\"id\": \"ros.json\",\n'
    s += '\t\"reports\": [\n'

    packs = iter(packages)
    s += jsonifyPackage(next(packs))
    for p in packs:
        s += ',\n' + jsonifyPackage(p)
    s += '\n'

    s += '\t]\n'
    s += '}]'
    return s


packages = makePackageList('/opt/ros/hydro/share')
packages = scorer.scorePackages(packages)
f = open('ros.json', 'w')
f.write(jsonifyPackages(packages.values()).encode('ascii', 'xmlcharrefreplace'))
f.close()
print('package data written to ros.json')
