import pickle

from Filter.utils import WikiDataEntry


class Cache:

	def __init__(self):
		self.__cache = {}

	def loadCache(self, file):
		with open(file, 'rb') as cache_file:
			self.__cache = pickle.load(cache_file)

	def getEntry(self, wd_id):
		if wd_id not in self.__cache:
			self.__cache[wd_id] = CacheEntry()
		return self.__cache[wd_id]

	def deleteEntry(self, wd_id):
		del(self.__cache[wd_id])

	def saveCache(self, file):
		with open(f"{file}", 'wb') as cache_file:
			pickle.dump(self.__cache, cache_file, -1)


class CacheEntry:

	def __init__(self):
		#Defined by WikiData
		self.__languages = set()
		self.__labels = {}
		self.__alt_labels = {}
		self.__year = None
		self.__disambiguation_page = None
		self.__freebase = None
		#Defined by DBpedia
		self.__types = {}
		self.__foundDbpedia = None

	#Methods for WikiData
	def existsInLanguage(self, language):
		return language in self.__languages

	def exists(self):
		return len(self.__languages) > 0

	def isDisambiguationPage(self):
		return self.__disambiguation_page

	def addLanguage(self, language, wd_entry: WikiDataEntry):
		if not self.existsInLanguage(language):
			self.__languages.add(language)
			if wd_entry is not None:
				self.__labels[language] = wd_entry.getLabel()
				self.__alt_labels[language] = wd_entry.getAltLabels()
				if self.__year is None:
					self.__year = wd_entry.getYear()
				if self.__disambiguation_page is None:
					self.__disambiguation_page = wd_entry.getDisambiguation()
				if self.__freebase is None:
					self.__freebase = wd_entry.getFreebaseID()
			else:
				self.__labels[language] = ""
				self.__alt_labels[language] = ""

	def getLabel(self, language):
		if self.existsInLanguage(language):
			return self.__labels[language]
		return None

	def getAltLabels(self, language):
		if self.existsInLanguage(language):
			return self.__alt_labels[language]
		return None

	def getYear(self):
		return self.__year

	def getFreebase(self):
		return self.__freebase

	#Methods for DBpedia
	def isAssociatedTo(self, ner_type):
		if ner_type not in self.__types:
			self.__types[ner_type] = None
		return self.__types[ner_type]

	def setAssociationTo(self, ner_type, status):
		self.__types[ner_type] = status

	def setFoundInDBpedia(self, status):
		self.__foundDbpedia = status

	def foundInDBpedia(self):
		return self.__foundDbpedia


class RedirectionCache:

	def __init__(self):
		self.__redirections = {}

	def setRedirection(self, wd_id, redirected_wd_id):
		self.__redirections[wd_id] = redirected_wd_id

	def redirects(self, wd_id):
		redirects_to = None
		if wd_id in self.__redirections:
			if self.__redirections[wd_id] is None:
				redirects_to = False
			else:
				redirects_to = True
		return redirects_to

	def redirectsTo(self, wd_id):
		redirects = self.redirects(wd_id)
		if redirects is not None and redirects is True:
			return self.__redirections[wd_id]
		else:
			return None

	def loadCache(self, file):
		with open(file, 'rb') as cache_file:
			self.__redirections = pickle.load(cache_file)

	def saveCache(self, file):
		with open(f"{file}", 'wb') as cache_file:
			pickle.dump(self.__redirections, cache_file, -1)
