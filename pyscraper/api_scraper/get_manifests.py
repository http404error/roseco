import requests
from time import sleep # to not max out requests
import os.path

def getPackageNames(url):
	html = requests.get(url).text
	# unique char string for package listing
	start = """<img src="/icons/folder.gif" alt="[DIR]"> <a href=""" + '"'
	# char string after package name
	end = '/">'
	# find first start str and split on each start str
	pkg_rows = html[html.find(start)+len(start):].split(start)
	pkg_names = []
	for pkg_row in pkg_rows:
		pkg_names.append(pkg_row[:pkg_row.find(end)])
	
	return pkg_names

def makeManifestUrls(url, pkg_names):
	manifest_urls = []
	for pkg_name in pkg_names:
		manifest_urls.append(url + pkg_name + '/manifest.yaml')
	return manifest_urls

def writeManifestsToDir(manifest_urls, pkg_names, dir_path):
	for i in range(len(manifest_urls)):
		file_name = pkg_names[i] + '.yaml'
		print file_name
		save_path = os.path.join(dir_path, file_name)
		
		sleep(1.5)
		manifest = requests.get(manifest_urls[i]).text
		if "depends" not in manifest:
			print "NO DEPENDS, LOCKED OUT?"
		
		with open(save_path, 'w') as f:
			f.write(manifest)

def retrievePkgManifests(url, dir_path):
	pkg_names = getPackageNames(url = hydro_api)
	manifest_urls = makeManifestUrls(hydro_api, pkg_names)
	writeManifestsToDir(manifest_urls, pkg_names, dir_path)

if __name__ == '__main__':
	hydro_api = 'http://docs.ros.org/hydro/api/'
	dir_path = '/nfs/attic/smartw/users/reume04/roseco/pyscraper/yaml_manifest_scraper/manifests'
	retrievePkgManifests(url = hydro_api, dir_path = dir_path)