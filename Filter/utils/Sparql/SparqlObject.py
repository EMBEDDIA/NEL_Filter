from SPARQLWrapper.SPARQLExceptions import EndPointNotFound, EndPointInternalError
from SPARQLWrapper import SPARQLWrapper, JSON
import time
import logging

class SparqlObject:

	def __init__(self, service_url):
		self.__wrapper = SPARQLWrapper(service_url)
		self.__wrapper.setReturnFormat(JSON)
		self.__last_query_counter = 0
		self.__last_query_time = time.time()

	def verifyQueryTiming(self):
		current_time = time.time()
		if 0 >= current_time - self.__last_query_time > 1:
			self.__last_query_counter += 1
			if self.__last_query_counter >= 50:
				time.sleep(1)
		else:
			self.__last_query_counter = 0
			self.__last_query_time = current_time

	def executeQuery(self):
		try_again = True
		counter_tries = 0
		results = None
		while try_again:
			try:
				results = self.__wrapper.query().convert()
				try_again = False
			except EndPointNotFound as e:
				logging.error(f"Error while connecting to {self.__wrapper.endpoint}, waiting for 2 min")
				time.sleep(120)
				counter_tries += 1
				if counter_tries > 2:
					logging.error(f"Limit trying to connect to {self.__wrapper.endpoint}, returning None")
					try_again = False
					results = None
			except EndPointInternalError as e:
				logging.error(f"Timeout while querying {self.__wrapper.endpoint}, returning None")
				try_again = False
				results = None
			except Exception as e:
				logging.error(f"Exception while quering {self.__wrapper.endpoint}: {e}")
				found = False
				if hasattr(e, 'headers'):
					for header in e.headers._headers:
						if header[0] == "retry-after":
							logging.info(f"Sleeping for {header[1]}s + 5s more")
							time.sleep(float(header[1]) + 5)
							found = True
							break
					if found:
						if counter_tries < 2:
							try_again = True
							counter_tries += 1
						else:
							logging.error(f"Error despite waiting at {self.__wrapper.endpoint}, returning None")
							try_again = False
							results = None
					else:
						logging.error(f"Coudln't find retry-after while querying {self.__wrapper.endpoint}")
						try_again = False
						results = None
				else:
					logging.error(f"Unknown exception while querying {self.__wrapper.endpoint}: {e}")
					try_again = None
					results = None
		return results

	def setQuery(self, query):
		self.__wrapper.setQuery(query)

	def getEntryPoint(self):
		return self.__wrapper.endpoint