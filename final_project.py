import requests
import json
import re
import plotly.plotly as py
import plotly.graph_objs as go
from bs4 import BeautifulSoup
import sqlite3 as sqlite


BASEURL_WIKI = 'https://en.wikipedia.org/wiki/'
WIKI_CACHE = 'wiki_cache.json'
BASEURL_EDIT = 'https://en.wikipedia.org/w/index.php?title='
EDIT_BIT = '&action=history'
EDIT_CACHE = 'edit_cache.json'
DBNAME = 'WikiSearch.db'
edit_dict = {}
searched_words_list = []


try:
	f = open(WIKI_CACHE, "r") # CACHE_FNAME
	fileread = f.read()
	WIKI_DICT = json.loads(fileread)
	f.close()
	# print("loaded from cache json")
except:
	WIKI_DICT = {} # YT_CACHE = {}
	# print("making cache dict")

try:
	f = open(EDIT_CACHE, "r") # CACHE_FNAME
	fileread = f.read()
	EDIT_DICT = json.loads(fileread)
	f.close()
	# print("loaded from edit cache json")
except:
	EDIT_DICT = {} # YT_CACHE = {}
	# print("making edit cache dict")

try:
	f = open('data.json', "r")
	fr = f.read()
	search_dict = json.loads(fr)
	f.close()
except:
	search_dict = {}



# load stopwords from directory
f = open('stopwords.txt', 'r')
stopwords = []
for line in f.readlines()[7:]:
	stopwords.append(line.strip())
f.close()

class SearchedWord():
	def __init__(self, word, word_count_list, editdict):
		self.word = word
		self.word_count_list = word_count_list
		self.editdict = editdict

	def __str__(self):
		return "wiki result of :" + self.word + "\nMost used word: " + self.word_count_list[0][0] + " " + str(self.word_count_list[0][1]) + " times \nEdited by: " + self.editdict[0]['editorname'] + " in " + str(self.editdict[0]['yearstamp'])

	def __repr__(self):
		return self.word



def params_unique_combination(baseurl, params_d, wikiedit=0):
	sorted_keys = sorted(params_d.keys())
	res = []
	for k in sorted_keys:
		res.append("{}".format(params_d[k]))
	if wikiedit == 1:
		res.append("{}".format(EDIT_BIT))
	return baseurl + "".join(res)

def request_using_cache(url, keyword, cache_dict, cache_file,wikiedit=0):
	params = {}
	params["query"] = keyword
	query = params_unique_combination(url, params, wikiedit)
	# print(cache_dict)
	if query not in cache_dict:
		# print("retrieving data online...")
		resp = requests.get(query)
		page = resp.text
		# soup = BeautifulSoup(page, 'html.parser')
		cache_dict[query] = page
		cache_dump = json.dumps(cache_dict)
		cachefile = open(cache_file, "w")
		cachefile.write(cache_dump)
		cachefile.close()
	# else:
		# print("retrieving data from cache..")
	# print("...done!")
	return cache_dict[query]

def initialize_search_dict(keyword):	
	search_dict[keyword] = {}

def extract_information_wiki(keyword):
	html = request_using_cache(BASEURL_WIKI, keyword, cache_dict = WIKI_DICT, cache_file = WIKI_CACHE)
	soup = BeautifulSoup(html, 'html.parser')
	toc = soup.find(id='toc') # find table of contents
	shortcut = toc.find_all('li') # find lists
	hashtag_list = []
	for s in shortcut:
		hashtag_list.append(s.find('a')['href']) 
	search_dict[keyword]["hashtags"] = hashtag_list
	# print(len(search_dict[keyword]["hashtags"])) # find toc

	# time to find some words and their counts
	word_dict = {}
	for tag in soup.find_all('p'):
		for word in tag.text.split():
			if word not in stopwords:
				if word in word_dict:
					word_dict[word] += 1
				else:
					word_dict[word] = 1
	
	sorted_words = sorted(word_dict.items(), key=lambda x: x[1], reverse = True)
	if len(sorted_words) > 150:
		sorted_words_cropped = sorted_words[:150]
	else:
		sorted_words_cropped = sorted_words
	search_dict[keyword]["word_count"] = sorted_words_cropped


# scrape for history info
def crawl_edit(keyword):
	html = request_using_cache(BASEURL_EDIT, keyword, cache_dict = EDIT_DICT, cache_file = EDIT_CACHE, wikiedit=1)
	soup = BeautifulSoup(html, 'html.parser')
	edit_history = soup.find(id="pagehistory")
	search_dict[keyword]['edit_history'] = []
	edit_list=edit_history.find_all('li')
	for l in edit_list:
		try:
			editorname = l.find('a', {'class': 'mw-userlink'}).text
			timedate = l.find('a',{'class':'mw-changeslist-date'}).text
			timestamp = timedate[:2]
			yearstamp = timedate[-4:]
			changeamt = l.find('span', {'dir': 'ltr'}).text[1:-1]
			d = {}
			d['editorname'] = editorname
			d['timestamp'] = timestamp
			d['yearstamp'] = yearstamp
			d['changeamt'] = changeamt
			search_dict[keyword]['edit_history'].append(d)
		except:
			pass
	try:
		nextlink = find_next(soup)
		crawl_to_next(nextlink, keyword)
	except:
		pass

def find_next(soup):
	divi = soup.find(id='mw-content-text')
	nextlink = divi.find('a', {'class': 'mw-nextlink'})['href']
	return nextlink

def find_components_edit(query, keyword):
	html = cache_dict[query]
	soup = BeautifulSoup(html, 'html.parser')
	edit_history = soup.find(id="pagehistory")
	# search_dict[keyword]['edit_history'] = []
	edit_list=edit_history.find_all('li')
	for l in edit_list:
		try:
			editorname = l.find('a', {'class': 'mw-userlink'}).text
			timedate = l.find('a',{'class':'mw-changeslist-date'}).text
			timestamp = timedate[:2]
			yearstamp = timedate[-4:]
			changeamt = l.find('span', {'dir': 'ltr'}).text[1:-1]
			d = {}
			d['editorname'] = editorname
			d['timestamp'] = timestamp
			d['yearstamp'] = yearstamp
			d['changeamt'] = changeamt
			search_dict[keyword]['edit_history'].append(d)
		except:
			pass
	


# let's crawl to next pages recursively
def crawl_to_next(nextlink, keyword, cache_dict = EDIT_DICT, cache_file = EDIT_CACHE):
	baseurl = 'https://en.wikipedia.org'
	url = baseurl + nextlink

	params = {}
	query = url
	# print(cache_dict)
	if query not in cache_dict:
		# print("retrieving data online...")
		resp = requests.get(query)
		page = resp.text
		# soup = BeautifulSoup(page, 'html.parser')
		cache_dict[query] = page
		cache_dump = json.dumps(cache_dict)
		cachefile = open(cache_file, "w")
		cachefile.write(cache_dump)
		cachefile.close()

	find_components_edit(query, keyword)
	try:
		nextlink2 = find_next(soup)
		crawl_to_next(nextlink2, keyword)
	except:
		pass



def create_db_table(dbname):
	conn = sqlite.connect(dbname)
	cur = conn.cursor()
	statement = '''
		CREATE TABLE IF NOT EXISTS 'keys' (
		'kw_id' INTEGER PRIMARY KEY AUTOINCREMENT,
		'keyword' TEXT NOT NULL
		);
	'''
	cur.execute(statement)

	statement = '''
		CREATE TABLE IF NOT EXISTS 'history' (
		'edit_id' INTEGER PRIMARY KEY AUTOINCREMENT,
		'editor' TEXT NOT NULL,
		'time' INTEGER NOT NULL,
		'year' INTEGER NOT NULL,
		'change' INTEGER NOT NULL,
		'kw_id' INTEGER NOT NULL,
		FOREIGN KEY (kw_id) REFERENCES keys (kw_id)
		);
	'''
	cur.execute(statement)

	statement = '''
		CREATE TABLE IF NOT EXISTS 'words' (
		'word_id' INTEGER PRIMARY KEY AUTOINCREMENT,
		'word' TEXT NOT NULL,
		'count' INTEGER NOT NULL,
		'kw_id' INTEGER NOT NULL,
		FOREIGN KEY (kw_id) REFERENCES keys (kw_id)
		);
	'''
	cur.execute(statement)

	conn.commit()
	conn.close()


def insert_keyword(keyword):
	insertion = (None, keyword)
	statement = '''
		INSERT INTO keys VALUES (?,?);
	'''
	cur.execute(statement, insertion)
	conn.commit()

def insert_history(keyword, keynum):
	for history in search_dict[keyword]["edit_history"]:
		insertion = (None, history["editorname"], history["timestamp"], history["yearstamp"], history["changeamt"], keynum)
		statement = '''
			INSERT INTO history VALUES (?,?,?,?,?,?);
		'''
		cur.execute(statement, insertion)
	conn.commit()

def insert_words(keyword, keynum):
	for word in search_dict[keyword]["word_count"]:
		insertion = (None, word[0], word[1], keynum)
		statement = '''
			INSERT INTO words VALUES (?,?,?,?);
		'''
		cur.execute(statement, insertion)
	conn.commit()



def plot_edit_king(keyword):
	x_list = []
	y_list = []
	agg = {}
	if keyword in search_dict:
		for history in search_dict[keyword]["edit_history"]:
			agg[history["editorname"]] = []
		for history in search_dict[keyword]["edit_history"]:
			agg[history["editorname"]].append(int(history["changeamt"]))
		for key in agg:
			if len(agg[key]) > 1:
				agg[key] = [sum(agg[key])]
			x_list.append(key)
			y_list.append(agg[key][0])
	else:
		print("Keyword is invalid. Plot not drawn.")

	data = [go.Bar(
		x = x_list,
		y = y_list,
		base = 0,
		marker = dict(
			color = 'blue'
			),
		name = 'edit history by editor',
		opacity=0.6

		)]
	fig = go.Figure(data=data)
	py.plot(fig)

def plot_edit_years(keyword):
	x_list = []
	y_list = []
	agg = {}
	if keyword in search_dict:
		for history in search_dict[keyword]["edit_history"]:
			if history["yearstamp"] not in agg:
				agg[history["yearstamp"]] = 1
			else:
				agg[history["yearstamp"]] += 1
		for key in agg:
			x_list.append(key)
			y_list.append(agg[key])
	else:
		print("Keyword is invalid. Plot not drawn.")

	data = [go.Pie(
		labels = x_list,
		values = y_list,
		marker = dict(
			# color = 'red',
			line=dict(color='#FFFFFF', width=2)
			),
		name = 'edit history by year',
		)]
	fig = go.Figure(data=data)
	py.plot(fig)

def plot_edit_times(keyword):
	x_list = []
	y_list = []
	agg = {}
	if keyword in search_dict:
		for history in search_dict[keyword]["edit_history"]:
			if history["timestamp"] not in agg:
				agg[history["timestamp"]] = 1
			else:
				agg[history["timestamp"]] += 1
		for key in agg:
			x_list.append(key)
			y_list.append(agg[key])
	else:
		print("Keyword is invalid. Plot not drawn.")

	data = [go.Bar(
		x = x_list,
		y = y_list,
		base = 0,
		marker = dict(
			color = 'yellow'
			),
		name = 'edit history by time in a day',
		opacity=0.7

		)]
	fig = go.Figure(data=data)
	py.plot(fig)

def plot_word_count(keyword):
	# print("in plot keyword: " + keyword)
	x_list = []
	y_list = []
	try:
		for w in searched_words_list:
			if keyword == w.word:
				for word_tuple in w.word_count_list:
					x_list.append(word_tuple[0])
					y_list.append(word_tuple[1])
	except:
		print("Keyword is invalid. Plot not drawn.")

	data = [go.Bar(
		x = x_list,
		y = y_list,
		base = 0,
		marker = dict(
			color = 'green'
			),
		name = 'word count in Wiki article for {}'.format(keyword),
		opacity=0.6

		)]
	fig = go.Figure(data=data)
	py.plot(fig)


def update_search_list(keyword):
	initialize_search_dict(keyword)
	extract_information_wiki(keyword)
	crawl_edit(keyword)
	searched_words_list.append(SearchedWord(keyword, search_dict[keyword]["word_count"], search_dict[keyword]["edit_history"]))

def update_db(keyword, keynum):
	insert_keyword(keyword)
	insert_history(keyword, keynum)
	insert_words(keyword, keynum)


def load_text(textfile):
    with open(textfile) as f:
        return f.read()

def interactive_prompt():
	help_text = load_text('help.txt')
	suboption = load_text('suboption.txt')
	response = ''
	keyword = ''
	keynumber = 0
	cur.execute("SELECT kw_id FROM keys ORDER BY kw_id DESC LIMIT 1")
	kn = cur.fetchone()
	if kn != None:
		keynumber = kn[0]

	while response != 'exit':
		response = input("Enter a keyword or *help for help: ")
		if response == 'exit':
			pass
		elif response == '*help':
			print(help_text)

		elif response == '*history':
			for sw in searched_words_list:
				print(sw, "\n")

		elif response[0] != '*':
			keyword = response
			cur.execute("SELECT * FROM keys WHERE keyword = ?", (keyword,))
			data = cur.fetchone()
			update_search_list(keyword)
			if data is None:
				keynumber += 1
				update_db(keyword, keynumber)
			print("Your keyword is {}.".format(keyword))
			print(suboption)
			subresp = ''
			while subresp != '*back':
				# print(keyword)
				subresp = input("Enter an option: ")
				if subresp == '*back':
					pass
				elif subresp == '*word count':
					plot_word_count(keyword)
				elif subresp == '*edit king':
					plot_edit_king(keyword)
				elif subresp == '*edit by year':
					plot_edit_years(keyword)
				elif subresp == '*edit by time':
					plot_edit_times(keyword)
				else:
					print("Option invalid: {}".format(subresp))


		else:
			print("Sorry. Command not understood.  {}".format(response))

	with open('data.json', 'w') as f:
		json.dump(search_dict,f)

if __name__ == '__main__':
	create_db_table(DBNAME)
	conn = sqlite.connect(DBNAME) # start database connection
	cur = conn.cursor()

	interactive_prompt()

	conn.close()

















