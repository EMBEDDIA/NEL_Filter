import time

from SPARQLWrapper import SPARQLWrapper, JSON
from SPARQLWrapper.SPARQLExceptions import EndPointNotFound
from stop_words import get_stop_words, StopWordError
import regex
#Change the rapidfuzz for fuzzywuzzy if it is needed the original implementation
from rapidfuzz import fuzz


class FilteringNEL:

	def __init__(self, lang, input_file_path, output_file_path, comment_token, freeling=False, sep="|", tokens_col=0, lit_col=1, meto_col=None, wd_col=2, last_nil=True, no_candidates=1, start_at=0, skip_header=False, filter=True, search_name=True):
		self.__db_types = {
			"loc": ["dbo:Location", "dbo:Settlement", "dbo:Region", "dbo:Building", "dbo:Village",
					"umbel-rc:Country", "yago:YagoGeoEntity"],
			"org": ["dbo:Organisation", "umbel-rc:Business", "dbc:Supraorganizations", "yago:YagoGeoEntity"],
			"pers": ["foaf:Person", "dbo:Person", "dbo:Agent", "dul:SocialPerson"],
			"per": ["foaf:Person", "dbo:Person", "dbo:Agent", "dul:SocialPerson"],
			"prod": ["dbo:Work", "dbo:Newspaper", "umbel-rc:Business"],
			"humanprod": ["dbo:Work", "dbo:Newspaper", "umbel-rc:Business"]
		}
		self.__search_name = search_name
		self.__tokens_col = tokens_col
		self.__lit_col = lit_col
		self.__meto_col = meto_col
		self.__wd_col = wd_col
		self.__lang = lang
		self.__supported_lang = False
		self.__sparql = SPARQLWrapper("http://dbpedia.org/sparql")

		# Supported by the English DBpedia
		if self.__lang in ["en", "de", "nl", "it", "es", "fr", "ja", "ar", "pl", "pt", "ru", "zh"]:
			self.__supported_lang = True
		self.__sparql_chapter = None
		self.__wikidata_www_chapters = None
		# Supported by the DBpedia Chapter
		if self.__lang in ["ar", "eu", "ca", "cs", "nl", "eo", "fr", "el", "de", "id", "it", "ja", "ko", "pl", "pt", "es", "sv", "uk"]:
			#Some chapters use www in the wikidata url, while other don't
			self.__wikidata_www_chapters = ["es", "eu", "de", "ja"]
			self.__sparql_chapter = SPARQLWrapper(f"http://{self.__lang}.dbpedia.org/sparql")

		try:
			self.__stop_words_list = get_stop_words(lang)
		except StopWordError:
			self.__stop_words_list = self.loadFileStopwords()
		self.__input_file_path = input_file_path
		self.__output_file_path = output_file_path
		self.__comment_token = comment_token
		self.__output_file = None
		self.__last_query_time = time.time()
		self.__last_query_time_chapter = time.time()
		self.__last_query_counter = 0
		self.__last_query_counter_chapter = 0
		self.__news_date = None
		self.__freeling = freeling
		self.__sep = sep
		self.__last_nil = last_nil
		self.__no_candidates = no_candidates
		self.__start_at = start_at
		self.__skip_header = skip_header
		self.__filter = filter

	def loadFileStopwords(self):
		stopwords = []
		with open(f"./stopwords/{self.__lang}.txt") as stopwords_file:
			line = stopwords_file.readline()
			while line:
				line = line.rstrip('\n')
				if line == "" or line.startswith("# "):
					line = stopwords_file.readline()
					continue
				stopwords.append(line)
				line = stopwords_file.readline()
		return stopwords

	def verifyQueryTiming(self, entrypoint):
		if entrypoint == self.__sparql:
			self.verifyQueryTimingEnglish()
		else:
			self.verifyQueryTimingChapter()

	def verifyQueryTimingEnglish(self):
		current_time = time.time()
		if 0 >= current_time - self.__last_query_time > 1:
			self.__last_query_counter += 1
			if self.__last_query_counter >= 50:
				time.sleep(1)
		else:
			self.__last_query_counter = 0
			self.__last_query_time = current_time

	def verifyQueryTimingChapter(self):
		current_time = time.time()
		if 0 >= current_time - self.__last_query_time_chapter > 1:
			self.__last_query_counter_chapter += 1
			if self.__last_query_counter_chapter >= 50:
				time.sleep(1)
		else:
			self.__last_query_counter_chapter = 0
			self.__last_query_time_chapter = current_time

	def askExistsQuery(self, wd_id, entrypoint):
		wikidata_complement = ""
		if entrypoint == self.__sparql:
			wikidata_complement = "www."
		elif self.__lang in self.__wikidata_www_chapters:
			wikidata_complement = "www."
		query_base = f"""
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                    PREFIX wd: <http://{wikidata_complement}wikidata.org/entity/>
                    PREFIX umbel-rc: <http://umbel.org/umbel/rc/>
                    PREFIX dbc: <http://dbpedia.org/resource/Category>
                    PREFIX dbo: <http://dbpedia.org/ontology/>
                    PREFIX yago: <http://dbpedia.org/class/yago/>
                    PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl>
                    ASK {{
                        ?sub a ?type .
                        ?sub owl:sameAs wd:{wd_id} .
                    }}
                """
		self.verifyQueryTiming(entrypoint)
		entrypoint.setQuery(query_base)
		entrypoint.setReturnFormat(JSON)
		try_again = True
		try_counter = 0
		result = {"boolean": False}
		while try_again:
			try:
				result = entrypoint.query().convert()
				try_again = False
			except EndPointNotFound as e:
				print(e)
				time.sleep(60)
				try_counter += 1
				if try_counter > 2:
					exit(1)
		return result["boolean"]

	def askDomainQuery(self, db_types, wd_id, entrypoint):
		if self.__supported_lang or entrypoint == self.__sparql_chapter:
			search_in = []
			for db_type in db_types:
				search_in += self.__db_types[db_type]
			search_in = set(search_in)
			search_in = ", ".join(search_in)
			search_in = f"FILTER(?type IN ({search_in}))"
		else:
			search_in = ""
		wikidata_complement = ""
		if entrypoint == self.__sparql:
			wikidata_complement = "www."
		elif self.__lang in self.__wikidata_www_chapters:
			wikidata_complement = "www."
		query_base = f"""
					PREFIX owl: <http://www.w3.org/2002/07/owl#>
					PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
					PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
					PREFIX foaf: <http://xmlns.com/foaf/0.1/>
					PREFIX wd: <http://{wikidata_complement}wikidata.org/entity/>
					PREFIX umbel-rc: <http://umbel.org/umbel/rc/>
					PREFIX dbc: <http://dbpedia.org/resource/Category>
					PREFIX dbo: <http://dbpedia.org/ontology/>
					PREFIX yago: <http://dbpedia.org/class/yago/>
					PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl>
					ASK {{
						?sub a ?type .
						{search_in}
						?sub owl:sameAs wd:{wd_id} .
					}}
				"""
		self.verifyQueryTiming(entrypoint)
		entrypoint.setQuery(query_base)
		entrypoint.setReturnFormat(JSON)
		try_again = True
		try_counter = 0
		result = {"boolean": False}
		while try_again:
			try:
				result = entrypoint.query().convert()
				try_again = False
			except EndPointNotFound as e:
				print(e)
				time.sleep(60)
				try_counter += 1
				if try_counter > 2:
					exit(1)
		return result["boolean"]

	def createQuery(self, db_types, wd_id, entrypoint):
		sorting = ""
		sort_by = []
		select_elements = ["?sub", "?lbl"]
		query_dob = ""
		if self.__news_date is not None:
			for db_type in db_types:
				if db_type in ["pers", "per"]:
					query_dob = f"""
					   OPTIONAL{{
						   ?sub dbo:birthDate ?dob
						   BIND(REPLACE(?dob, "-.+$", "") AS ?year)
					   }}
					"""
					select_elements.append("?year")
		if len(sort_by) > 0:
			sort_by = " ".join(sort_by)
			sorting = f"ORDER BY {sort_by}"
		select = " ".join(select_elements)

		wikidata_complement = ""
		if entrypoint == self.__sparql:
			wikidata_complement = "www."
		elif self.__lang in self.__wikidata_www_chapters:
			wikidata_complement = "www."

		query_base = f"""
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX wd: <http://{wikidata_complement}wikidata.org/entity/>
					PREFIX dbo: <http://dbpedia.org/ontology/>
                    SELECT {select} WHERE {{
                        ?sub owl:sameAs wd:{wd_id}.
                        ?sub rdfs:label ?lbl .
                        FILTER(langMatches(lang(?lbl), "{self.__lang}"))
                        {query_dob}
                    }}
                    GROUP BY ?sub
                    {sorting}
                """
		return query_base

	def runQuery(self, nel_query, wd_id, entrypoint):
		self.verifyQueryTiming(entrypoint)
		entrypoint.setQuery(nel_query)
		entrypoint.setReturnFormat(JSON)
		try_again = True
		try_counter = 0
		parsed_results = None
		while try_again:
			try:
				results = entrypoint.query().convert()
				try_again = False
				parsed_results = {}
				if len(results["results"]["bindings"]) == 0:
					parsed_results[wd_id] = None
					#return None
				else:
					for result in results["results"]["bindings"]:
						if "year" in result:
							year = result["year"]["value"]
							if year == "":
								year = 0 #This means that the year was negative
							if int(year) > self.__news_date + 10:
								return None
						parsed_results[wd_id] = result["lbl"]["value"]
			except EndPointNotFound as e:
				print(e)
				time.sleep(60)
				try_counter += 1
				if try_counter > 2:
					exit(1)
		return parsed_results

	def processQuery(self, supported_tags, wd_id, wd_ids_to_skip, results, last_position, entrypoint):
		nel_query = self.createQuery(supported_tags, wd_id, entrypoint)
		temp_results = self.runQuery(nel_query, wd_id, entrypoint)
		if temp_results is None:  # We must skip this person
			wd_ids_to_skip.add(wd_id)
		elif temp_results[wd_id] is None:
			if entrypoint == self.__sparql and self.__sparql_chapter is not None:
				self.processQuery(supported_tags, wd_id, wd_ids_to_skip, results, last_position, self.__sparql_chapter)
			else:
				results.update(temp_results)
		else:
			results.update(temp_results)

	def processToken(self, tokens, tags_to_process, wd_ids, shift_to_comment=False, nested=False):
		results = {}
		wd_ids_to_skip = set()
		last_position = []
		tokens_as_string = ""
		ask_dob = False
		if self.__filter:
			supported_tags = []
			for tag in tags_to_process:
				if tag in self.__db_types.keys():
					supported_tags.append(tag)
					if tag in ["per", "pers"]:
						ask_dob = True
			if len(supported_tags) == 0:
				return "|".join(wd_ids)
			label_keys = []
			comment_keys = []
			if self.__supported_lang or self.__sparql_chapter is not None:
				for token in tokens:
					if regex.search("\d", token):
						continue
					if token == ",":
						if not nested and len(label_keys) > 0:
							shift_to_comment = True
						elif nested and len(comment_keys) > 0:
							shift_to_comment = False
					if not shift_to_comment:
						tokens_as_string += f"{token} "

			for wd_id in wd_ids:
				if wd_id in ["_", ""]:
					wd_ids_to_skip.add(wd_id)
				elif wd_id in ["NIL"]:
					continue
				elif self.askExistsQuery(wd_id, self.__sparql):
					if self.askDomainQuery(supported_tags, wd_id, self.__sparql):
						if self.__search_name or ask_dob:
							if self.__supported_lang:
								self.processQuery(supported_tags, wd_id, wd_ids_to_skip, results, last_position, self.__sparql)
							elif self.__sparql_chapter is not None:
								self.processQuery(supported_tags, wd_id, wd_ids_to_skip, results, last_position, self.__sparql_chapter)
							else:
								results[wd_id] = None
						else:
							results[wd_id] = None
					else:
						last_position.append(wd_id)
						results[wd_id] = None
				elif self.__sparql_chapter is not None and self.askExistsQuery(wd_id, self.__sparql_chapter):
					if self.askDomainQuery(supported_tags, wd_id, self.__sparql_chapter):
						if self.__search_name or ask_dob:
							self.processQuery(supported_tags, wd_id, wd_ids_to_skip, results, last_position, self.__sparql_chapter)
						else:
							results[wd_id] = None
					else:
						last_position.append(wd_id)
						results[wd_id] = None
		else:
			for wd_id in wd_ids:
				if wd_id in ["_", ""]:
					wd_ids_to_skip.add(wd_id)
				elif wd_id in ["NIL"]:
					continue
				else:
					results[wd_id] = None
		return self.processResults(results, wd_ids_to_skip, last_position, wd_ids, tokens_as_string)

	def processResults(self, results, wd_ids_to_skip, last_position, wd_ids, tokens_as_string):
		final_results = []
		catch_nil = False
		if (self.__supported_lang or self.__sparql_chapter is not None) and self.__filter:
			best_result = ""
			if self.__search_name:
				best_result = "NIL"
				best_distance = 500 #I just consider that the distances should be smaller
				for (key, value) in results.items():
					if value is not None and value != "":
						#distance = editdistance.eval(value.lower(), tokens_as_string.lower())
						distance = 100 - fuzz.WRatio(value.lower(), tokens_as_string.lower())
						if distance < best_distance:
							best_distance = distance
							best_result = key
			for wd_id in wd_ids:
				if wd_id == best_result or wd_id in wd_ids_to_skip or wd_id in last_position:
					continue
				if wd_id == "NIL":
					catch_nil = True
				final_results.append(wd_id)
			if len(last_position) > 0 and best_result != "NIL" and not catch_nil:
				final_results.append("NIL")
				catch_nil = True
			for wd_id in last_position:
				final_results.append(wd_id)
			if best_result != "":
				final_results.insert(0, best_result)
			if best_result == "NIL":
				catch_nil = True
		else:
			for (key, value) in results.items():
				final_results.append(key)
			#final_results.append("NIL")
			#catch_nil = True

		if self.__last_nil:
			if not catch_nil:
				while len(final_results) > self.__no_candidates - 1:
					final_results.pop()
				final_results.append("NIL")
			else:
				while len(final_results) > self.__no_candidates:
					final_results.pop()
		else:
			while len(final_results) > self.__no_candidates:
				final_results.pop()

		return "|".join(final_results)

	def readFile(self):
		if self.__start_at == 0:
			self.__output_file = open(self.__output_file_path, "w")
		else:
			self.__output_file = open(self.__output_file_path, "a")
		skip_lines = 0
		with open(self.__input_file_path) as input_file:
			if self.__start_at > 0:
				while self.__start_at > skip_lines:
					line = input_file.readline()
					skip_lines += 1
			else:
				if self.__skip_header:
					line = input_file.readline() #Header
					line = line.rstrip('\n')
					if not self.__freeling:
						self.printOutput(line)
				line = input_file.readline()
			tokens = []
			rows = []
			tag_lit = ""
			wd_ids = []
			tags_to_process = []
			while line:
				line = line.rstrip('\n')
				if line == "":
					if len(tokens) > 0:
						result = self.processToken(tokens, tags_to_process, wd_ids)
						self.generateNELOutput(rows, result)
						tokens = []
						rows = []
						tag_lit = ""
						tags_to_process = []
						wd_ids = []
					self.printOutput(line)
				elif self.__comment_token is not None and line.startswith(self.__comment_token):
					if line.startswith("# date = "):
						self.__news_date = int(regex.search("\d\d\d\d", line)[0])
					if not self.__freeling:
						if tag_lit == "":
							self.printOutput(line)
						else:
							rows.append(line)
				else:
					columns = line.split("\t")
					print(f"{line}\n")
					if columns[self.__lit_col] == "O":
						if len(tokens) > 0:
							result = self.processToken(tokens, tags_to_process, wd_ids)
							self.generateNELOutput(rows, result)
							tokens = []
							rows = []
							tag_lit = ""
							tags_to_process = []
							wd_ids = []
						#self.printOutput(line)
						self.generateNELOutput([columns], None)
					else:
						if columns[self.__lit_col][0] == "B":
							if len(tokens) > 0:
								result = self.processToken(tokens, tags_to_process, wd_ids)
								self.generateNELOutput(rows, result)
								tokens = []
								rows = []
								tag_lit = ""
								tags_to_process = []
								wd_ids = []
							tag_lit = columns[self.__lit_col][2:].lower()
							tags_to_process.append(tag_lit)
							wd_ids = columns[self.__wd_col].split(self.__sep)
						if columns[self.__lit_col][0] == "I" and tag_lit == "": #Just in case the labeling isn't the correct one
							tag_lit = columns[self.__lit_col][2:].lower()
							tags_to_process.append(tag_lit)
							wd_ids = columns[self.__wd_col].split(self.__sep)
						if self.__meto_col is not None and columns[self.__meto_col][0] != "O":
							meto_tag = columns[self.__meto_col][2:].lower()
							meto_tag = regex.sub("\..+$", "", meto_tag)
							if meto_tag not in tags_to_process:
								tags_to_process.append(meto_tag)
						rows.append(columns)
						tokens.append(columns[self.__tokens_col])
				line = input_file.readline()
			if len(tokens) > 0:
				result = self.processToken(tokens, tags_to_process, wd_ids)
				self.generateNELOutput(rows, result)
		self.__output_file.close()

	def printOutput(self, line):
		self.__output_file.write(f"{line}\n")


	def generateNELOutput(self, rows, result):
		for columns in rows:
			if type(columns) is list:
				if result is not None:
					columns[self.__wd_col] = result
					if self.__meto_col is not None and columns[self.__meto_col] != "O": #For METO
						columns[self.__wd_col + 1] = result
				if len(columns) == 10 and self.__freeling:
					del columns[-1]
				nel_output = "\t".join(columns)
				self.printOutput(nel_output)
			else:
				self.printOutput(columns)


input_path=""
output_path=""
comment_symbol="# "
language=""
nel = FilteringNEL(language, input_path, output_path, comment_symbol, freeling=False)
nel.readFile()

