#!/usr/bin/env python

import os
import fnmatch

# XML parsing
import xml.dom.minidom

def makeDataFileList(komodo_dir):
    data = []

    for root,dirnames,filenames in os.walk(komodo_dir):
        for filename in fnmatch.filter(filenames, 'roskomodo*.xml'):
            data.append(os.path.join(root, filename))

    print ' Found', len(data), 'data files in', komodo_dir
    return data


# Generate a dictionary of package runtime.  Key is the package name,
# value is the number of seconds that package ran in total
def makeDataList(komodo_dir):
    komodo_dict = {}

    # Parse the files one by one
    for f in makeDataFileList(komodo_dir):
        try:
            dom = xml.dom.minidom.parse(f)
        except:
            'Bad Parse:', f

        # Extract the information, adding to the values if necessary
        try:
            launches = dom.getElementsByTagName('launch')
            for launch in launches:                
                # set name
                name = ''
                for child in launch.childNodes:
                    if (child.nodeName == 'package'):
                        name = child.firstChild.data
                if (name == ''):
                    print 'Couldnt find package name!'
                
                # set time
                if name in komodo_dict:
                    time = komodo_dict[name]
                else:
                    time = 0.0
                
                for child in launch.childNodes:
                    if (child.nodeName == 'duration'):
                        time += float(child.firstChild.data)
                
                # fill dict entry
                komodo_dict[name] = time
                
        except:
            print 'Parse problem in', f

    return komodo_dict

if __name__ == "__main__":
    data = makeDataList('./komodo')
    print data
