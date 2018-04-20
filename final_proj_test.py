import unittest
import sqlite3
from final_project import *


class TestWebData(unittest.TestCase):
	def setUp(self):
		f = open(WIKI_CACHE, "r") # CACHE_FNAME
		fileread = f.read()
		self.cachedict = json.loads(fileread)
		f.close()

		self.keyword = 'michigan'
		update_search_list(self.keyword)

		self.puc = params_unique_combination(BASEURL_WIKI, {"query": self.keyword})
		# print("url combo: ", self.puc)

	def test_cache(self):
		self.assertIn('https://en.wikipedia.org/wiki/michigan', self.cachedict)

	def test_crawl(self):
		try:
			crawl_edit(self.keyword)
		except:
			self.fail()


class TestDB(unittest.TestCase):

	def setUp(self):
		self.conn = sqlite3.connect(DBNAME)
		self.cur = self.conn.cursor()

	def test_keys_table(self):
		stmt = 'SELECT keyword FROM keys'
		results = self.cur.execute(stmt)
		r_list = results.fetchall()

		self.assertIn(('michigan',), r_list)
		self.assertEqual('omelet', r_list[5][0])

	def test_history_table(self):

		stmt = '''
			SELECT editor, change, year
			FROM history as h
			JOIN keys as k ON h.kw_id = k.kw_id
			WHERE k.keyword IS 'michigan'
			ORDER BY change DESC LIMIT 10
		'''

		results = self.cur.execute(stmt)
		r_list = results.fetchall()

		# print(r_list)

		self.assertEqual(r_list[0][0],'GreenC bot')
		self.assertEqual(r_list[0][1], 382)
		self.assertEqual(r_list[0][2], 2017)

		self.assertEqual(r_list[3][0],'7&6=thirteen')
		self.assertEqual(r_list[3][1], 294)
		self.assertEqual(r_list[3][2], 2017)

	def test_words_table(self):

		stmt = '''
			SELECT word, count
			FROM words as w
			JOIN keys as k ON w.kw_id = k.kw_id
			WHERE k.keyword IS 'omelet'
			ORDER BY count DESC LIMIT 10
		'''
		results = self.cur.execute(stmt)
		r_list = results.fetchall()

		self.assertEqual(r_list[0][0],'omelette')
		self.assertEqual(r_list[0][1], 15)


	def tearDown(self):
		self.conn.close()


class TestPlot(unittest.TestCase):
	def setUp(self):
		self.keyword = 'michigan'
		update_search_list(self.keyword)

	def test_wordcount_plot(self):
		try:
			plot_word_count(self.keyword)
		except:
			self.fail()

	def test_editking_plot(self):
		try:
			plot_edit_king(self.keyword)
		except:
			self.fail()

	def test_edit_years(self):
		try:
			plot_edit_years(self.keyword)
		except:
			self.fail()

	def test_edit_times(self):
		try:
			plot_edit_times(self.keyword)
		except:
			self.fail()


unittest.main(verbosity=2)

