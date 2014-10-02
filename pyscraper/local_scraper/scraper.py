#!/usr/bin/env python

from people import Person, PersonSet
from package import *
from operator import itemgetter

# Returns the set of all maintainers among the packages
def getMaintainers(packages):
    maintainers = reduce(set.union, [p.maintainers.people for p in packages.values()])
    return maintainers

### Scoring Functions for Ranked and Filter ###

# Scores packages on how many packages depend directly on them
def pkgsDepended(packages):
    score = {}
    for p in packages.values():
        all_depended = set()
        all_depended |= p.buildtool_depended
        all_depended |= p.build_depended
        all_depended |= p.run_depended
        score[p.name] = len(all_depended)
    return score

# Scores packages on how many packages depend on them indirectly
def pkgsDependedClosed(packages):
    score = {}
    for p in packages.values():
        all_depended = set()
        all_depended |= p.closed_buildtool_depended
        all_depended |= p.closed_build_depended
        all_depended |= p.closed_run_depended
        score[p.name] = len(all_depended)
    return score

# Scores packages on the number of maintainers
def pkgsMaintainers(packages):
    score = {}
    for p in packages.values():
        score[p.name] = len(p.maintainers)
    return score

# Scores packages on the number of authors
def pkgsAuthors(packages):
    score = {}
    for p in packages.values():
        score[p.name] = len(p.authors)
    return score

# Scores maintainers on how many packages they maintain
def mtnrsCount(packages):
    score = {}
    maintainers = getMaintainers(packages)
    for m in maintainers:
        score[m.name] = 0
    for p in packages.values():
        for i in p.maintainers.people:
            score[i.name] += 1
    return score                    

# Scores maintainers on how many packages depend on their work
def mtnrsDepended(packages):
    score = {}
    maintainers = getMaintainers(packages)
    for m in maintainers:
        #small_set = set()
        big_set = set()
        for p in packages.values():
            for person in p.maintainers.people:
                if person.name == m.name:
                    #small_set.add(p.name)
                    big_set |= p.buildtool_depended
                    big_set |= p.build_depended
                    big_set |= p.run_depended
        score[m.name] = len(big_set)
        
    return score

# Sorts a dict by value and prints on separate lines
def printSortedDict(items, desc = True):
    # Sort by value
    sorted_items = sorted(items.iteritems(),
                          key=itemgetter(1),
                          reverse=desc)
    for key, val in sorted_items:
        print key, val

# Kind of like filter(), but for dicts
def filterDict(items, condition):
    #output = {}
    #for key, val in items.iteritems():
    #    if condition(val):
    #        output[key] = val
    #return output
    return dict((k,v) for k, v in items.iteritems() if condition(v))

# Given a dict, print the keys on separate lines
def printDictKeys(items):
    for key, val in items.iteritems():
        print key

# Returns a string of all the maintainer emails for a package, separated by spaces
def getMaintainerEmails(package):
    emailstring = ''
    for person in package.maintainers.people:
        emailstring += str(person.emails) + ' '
    return emailstring
    
if __name__ == '__main__':

    # packages is a dict
    packages = makePackageList('/opt/ros/hydro/share')
    
    print 'Maintainers ordered by most packages maintained:'
    printSortedDict(mtnrsDepended(packages))
    
    print 'Packages ordered by most directly depended on:'
    printSortedDict(pkgsDepended(packages))
    
    print 'Packages ordered by most implicitly depended on:'
    printSortedDict(pkgsDependedClosed(packages))
    
    print 'Packages with nothing depending on them:'
    printDictKeys(filterDict(packages, lambda p: len(p.getAllDepended()) == 0))
    
    print 'Packages with no maintainers:'
    printDictKeys(filterDict(packages, lambda p: len(p.maintainers) == 0))
    
    print 'Packages with no authors:'
    printDictKeys(filterDict(packages, lambda p: len(p.authors) == 0))

    print 'Packages maintained by someone with a willowgarage.com email:'
    printDictKeys(filterDict(packages, lambda p: getMaintainerEmails(p).find('willowgarage') != -1))
