#!/usr/bin/env python

import os
import fnmatch
import random

# XML parsing
import xml.dom.minidom

from people import Person, PersonSet
import komodo
import re

# Holds all of the information for a single ROS package
class Package:
    def __init__(self, name):
        self.name = name
        self.isMetapackage = False
        self.authors = PersonSet()
        self.maintainers = PersonSet()
        self.description = ''
        self.licenses = None
        self.url = None

        # Package description
        self.quality = 1.0
        self.shape = "rect"
        self.scale = 1.0

        # Used in package scoring
        self.impact = 0.0
        self.health = 0.0
        self.runtime = 0.0
        # Number of packages depending on this one, order denotes degree of separation
        # Number of first order deps, second order deps, third order deps, etc.
        self.buildtool_dep_orders_list = []
        self.build_dep_orders_list = []
        self.run_dep_orders_list = []

        # String describing git issue counts/types
        self.git_issues = ''

        # Package dependencies
        self.buildtool_depend = None
        self.build_depend = None
        self.run_depend = None

        # Packages that depend on this one
        self.buildtool_depended = set()
        self.build_depended = set()
        self.run_depended = set()

        # Transitive closure of the dependencies
        self.closed_buildtool_depend = set()
        self.closed_build_depend = set()
        self.closed_run_depend = set()

        # Transitive closure of the packages that depend on this one
        self.closed_buildtool_depended = set()
        self.closed_build_depended = set()
        self.closed_run_depended = set()

        # Packages that depend on this one separated by order
        # Format is a list of sets, each successive set being an order of separation
        # The first set in the list will always be the same as the corresponding
        # buildtool/build/run_depended set
        self.buildtool_dep_orders = []
        self.build_dep_orders = []
        self.run_dep_orders = []

    def __str__(self):
        s = self.name

        # Authors
        s += '\n  authors:'
        for author in self.authors.people:
            s += '\n    ' + author.name

        # Maintainers
        s += '\n  maintainers:'
        for maintainer in self.maintainers.people:
            s += '\n    ' + maintainer.name

        s += self._show_set('licences', self.licenses)
        s += self._show_set('urls', self.url)


        s += '\n  dependencies:'
        s += self._show_number('buildtool',
                               self.buildtool_depend,
                               self.closed_buildtool_depend)
        s += self._show_number('build',
                               self.build_depend,
                               self.closed_build_depend)
        s += self._show_number('run',
                               self.run_depend,
                               self.closed_run_depend)

        s += '\n  depended on:'
        s += self._show_number('buildtool',
                               self.buildtool_depended,
                               self.closed_buildtool_depended)
        s += self._show_number('build',
                               self.build_depended,
                               self.closed_build_depended)
        s += self._show_number('run',
                               self.run_depended,
                               self.closed_run_depended)

        return s


    def _show_set(self, name, s):
        retval = '\n  {0}: '.format(name)
        for element in s:
            retval += '\n    ' + element
        return retval

    def _show_number(self, name, s, sc):
        return '\n    {0}: {1} ({2})'.format(name, len(s), len(sc))

    def getAllDepend(self):
        return self.buildtool_depend | self.build_depend | self.run_depend

    def getAllDepended(self):
        return self.buildtool_depended | self.build_depended | self.run_depended

def makePackageFileList(ros_root):
    packages = []

    for root,dirnames,filenames in os.walk(ros_root):
        for filename in fnmatch.filter(filenames, 'package.xml'):
            packages.append(os.path.join(root, filename))

    print 'Found', len(packages), 'package files in', ros_root
    return packages


# Generate a dictionary of all the packages.  Key is the package name,
# value is a Package instance with all of the information filled in.
def makePackageList(ros_root):
    package_list = []
    package_dict = {}

    komodo_dict = komodo.makeDataList('./komodo')

    # Parse the files one by one
    for f in makePackageFileList(ros_root):
        try:
            dom = xml.dom.minidom.parse(f)
        except:
            'Bad Parse:', f

        # Extract the information
        try:
            names = extractTag(dom, 'name')
            assert len(names) == 1

            package = Package(names[0])

            if len(dom.getElementsByTagName('metapackage')) > 0:
                package.isMetapackage = True

            for person in extractPeople(dom, 'author'):
                package.authors.add(person)

            for person in extractPeople(dom, 'maintainer'):
                package.maintainers.add(person)

            predescription = extractTag(dom, 'description')[0].strip().replace('\n','').replace('\r','').replace('\t','').replace('"','')
            package.description = re.sub(r'<.+?>', '', predescription)
            package.licenses = set(extractTag(dom, 'license'))
            package.url = set(extractTag(dom, 'url'))

            package.quality = random.random()
            package.shape = "rect"
            package.scale = 1.0
            if package.isMetapackage:
                package.scale = 2.4
            package.runtime = 0.0
            if (package.name in komodo_dict):
                package.runtime = komodo_dict[package.name]

            package.buildtool_depend = set(extractTag(dom, 'buildtool_depend'))
            package.build_depend = set(extractTag(dom, 'build_depend'))
            package.run_depend = set(extractTag(dom, 'run_depend'))

            package_list.append(package)
            package_dict[package.name] = package
        except:
            print 'Parse problem in', f

    # Calculate reverse dependencies for each package
    for p in package_list:
        for d in p.buildtool_depend:
            try:
                package_dict[d].buildtool_depended.add(p.name)
            except:
                pass
        for d in p.build_depend:
            try:
                package_dict[d].build_depended.add(p.name)
            except:
                pass
        for d in p.run_depend:
            try:
                package_dict[d].run_depended.add(p.name)
            except:
                pass

    for package in package_list:

        # Seed the closure lists with the immediate dependencies
        package.closed_buildtool_depend |= package.buildtool_depend
        package.closed_build_depend |= package.build_depend
        package.closed_run_depend |= package.run_depend
        package.closed_buildtool_depended |= package.buildtool_depended
        package.closed_build_depended |= package.build_depended
        package.closed_run_depended |= package.run_depended

        # Give reverse dependency order lists the first order (direct)
        package.buildtool_dep_orders.append(package.buildtool_depended)
        package.build_dep_orders.append(package.build_depended)
        package.run_dep_orders.append(package.run_depended)

    # Buildtool dependencies
    old_size = 0
    this_size = sum([len(p.closed_buildtool_depend) for p in package_list])
    print '  closing buildtool dependencies:',
    while this_size != old_size:
        print this_size,
        for package in package_list:
            for dep in package.closed_buildtool_depend:
                try:
                    package.closed_buildtool_depend = package.closed_buildtool_depend.union(package_dict[dep].closed_buildtool_depend)
                except:
                    pass

        old_size = this_size
        this_size = sum([len(p.closed_buildtool_depend) for p in package_list])
    print

    # Build dependencies.  This is clunky, but it works.  Keep adding
    # the dependencies of the packages in the dependency lists, until
    # the list stops growing.  Guaranteed to terminate in time linear
    # in the total number of packages.
    old_size = 0
    this_size = sum([len(p.closed_build_depend) for p in package_list])
    print '  closing build dependencies:',
    while this_size != old_size:
        print this_size,
        for package in package_list:
            for dep in package.closed_build_depend:
                try:
                    package.closed_build_depend = package.closed_build_depend.union(package_dict[dep].closed_build_depend)
                except:
                    pass

        old_size = this_size
        this_size = sum([len(p.closed_build_depend) for p in package_list])
    print

    # Run dependencies
    old_size = 0
    this_size = sum([len(p.closed_run_depend) for p in package_list])
    print '  closing run dependencies:',
    while this_size != old_size:
        print this_size,
        for package in package_list:
            for dep in package.closed_run_depend:
                try:
                    package.closed_run_depend = package.closed_run_depend.union(package_dict[dep].closed_run_depend)
                except:
                    pass

        old_size = this_size
        this_size = sum([len(p.closed_run_depend) for p in package_list])
    print


    # Reverse buildtool dependencies
    old_size = 0
    this_size = sum([len(p.closed_buildtool_depended) for p in package_list])
    print '  closing reverse buildtool dependencies:',
    while this_size != old_size:
        print this_size,
        for package in package_list:
            for dep in package.closed_buildtool_depended:
                try:
                    package.closed_buildtool_depended = package.closed_buildtool_depended.union(package_dict[dep].closed_buildtool_depended)
                except:
                    pass

            # Adds the successive degrees of dependency and removes the dependencies
            # that have already been recorded in any of the lower degrees
            order_deps = set(package.closed_buildtool_depended.union(package_dict[dep].closed_buildtool_depended))
            new_order_deps = set()
            for pkg in order_deps:
                if not any(pkg in item for item in package.buildtool_dep_orders):
                    new_order_deps.add(pkg)
            if len(new_order_deps) > 0:
                package.buildtool_dep_orders.append(new_order_deps)

        old_size = this_size
        this_size = sum([len(p.closed_buildtool_depended) for p in package_list])
    print


    # Reverse build dependencies
    old_size = 0
    this_size = sum([len(p.closed_build_depended) for p in package_list])
    print '  closing reverse build dependencies:',
    while this_size != old_size:
        print this_size,
        for package in package_list:
            for dep in package.closed_build_depended:
                try:
                    package.closed_build_depended = package.closed_build_depended.union(package_dict[dep].closed_build_depended)
                except:
                    pass

            # Adds the successive degrees of dependency and removes the dependencies
            # that have already been recorded in any of the lower degrees
            order_deps = set(package.closed_build_depended.union(package_dict[dep].closed_build_depended))
            new_order_deps = set()
            for pkg in order_deps:
                if not any(pkg in item for item in package.build_dep_orders):
                    new_order_deps.add(pkg)
            if len(new_order_deps) > 0:
                package.build_dep_orders.append(new_order_deps)

        old_size = this_size
        this_size = sum([len(p.closed_build_depended) for p in package_list])
    print

    # Reverse run dependencies
    old_size = 0
    this_size = sum([len(p.closed_run_depended) for p in package_list])
    print '  closing reverse run dependencies:',
    while this_size != old_size:
        print this_size,
        for package in package_list:
            for dep in package.closed_run_depended:
                try:
                    package.closed_run_depended = package.closed_run_depended.union(package_dict[dep].closed_run_depended)
                except:
                    pass

            # Adds the successive degrees of dependency and removes the dependencies
            # that have already been recorded in any of the lower degrees
            order_deps = set(package.closed_run_depended.union(package_dict[dep].closed_run_depended))
            new_order_deps = set()
            for pkg in order_deps:
                if not any(pkg in item for item in package.run_dep_orders):
                    new_order_deps.add(pkg)
            if len(new_order_deps) > 0:
                package.run_dep_orders.append(new_order_deps)

        old_size = this_size
        this_size = sum([len(p.closed_run_depended) for p in package_list])
    print

    return package_dict



# Extract data from a tag by tag name.  There might be more than one
# instance of a tag.
def extractTag(dom, tag):
    tag_list = []
    for element in dom.getElementsByTagName(tag):
        tag_list.append(str(element.firstChild.data))
    return tag_list


# Extract people from a tag.  There might be more than one instance of
# the tag.
def extractPeople(dom, tag):
    people_list = []

    for people in dom.getElementsByTagName(tag):
        person = Person(people.firstChild.data)

        emails = []
        for n,v in people.attributes.items():
            if n == 'email':
                person.addEmail(str(v))

        people_list.append(person)

    return people_list

if __name__ == '__main__':
    packages = makePackageList('/opt/ros/hydro/share')
