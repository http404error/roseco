from yaml import load

# Perhaps just a set of sets?

class Repo:
	def __init__(self, name):
		self.name = name # The name listed in the distribution file
		self.urls = None 
		self.repo_names = None # The repositories names on github
		self.status = None
		self.release_version = None

	def addUrlAndRepoName(self, url): 
		if 'git' not in url: return # Git API query won't work on non git
		
		repo_name = url.replace('https://github.com/','').replace('.git','')
		if self.urls == None:
			self.urls = set([url])
			self.repo_names = set([repo_name])
		else:
			self.urls.add(url)
			self.repo_names.add(repo_name)

	# def getUrls(self):
	# 	return self.urls

def getRepoData(dist_file):
	with open(dist_file, 'r') as open_file:
		data = load(open_file)
	return data['repositories']

def makeReposDict(dist_file):
	repo_data = getRepoData(dist_file)
	Repo_dict = {}
	for repo_name, data in repo_data.items():
		repo = Repo(repo_name)
		for to_check in ['doc','source','release']:
			if to_check in data:
				nstd = data[to_check]
				if 'url' in nstd:
					repo.addUrlAndRepoName(nstd['url'])
				if to_check == 'release' and 'version' in nstd:
					repo.release_version = nstd['version']

		if 'status' in data:
			repo.status = data['status']
			
		if repo.urls != None: Repo_dict[repo_name] = repo
	
	return Repo_dict

if __name__ == '__main__':
	Repos_dict = makeReposDict('distribution.yaml')
	# for r in Repos_dict.values():
	# 	print r.urls
	# 	print r.repo_names