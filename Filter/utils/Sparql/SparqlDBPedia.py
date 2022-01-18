from Filter.utils.Sparql.SparqlObject import SparqlObject


class SparqlDBPedia(SparqlObject):

	__db_types = {
		"loc": ["dbo:Location", "dbo:Place", "dbo:Settlement", "dbo:Region", "dbo:Building", "dbo:Village",
				"umbel-rc:Country", "yago:YagoGeoEntity"],
		"org": ["dbo:Organisation", "umbel-rc:Business", "dbc:Supraorganizations", "yago:YagoGeoEntity"],
		"per": ["foaf:Person", "dbo:Person", "dbo:Agent", "dul:SocialPerson"],
		"prod": ["dbo:Work", "dbo:Newspaper", "umbel-rc:Business", "schema:CreativeWork", "yago:TradeName106845599",
				 "yago:Product104007894"]
	}

	# Many chapters are offline
	#__chapters = ["ar", "eu", "ca", "cs", "nl", "eo", "fr", "el", "de", "id", "it", "ja", "ko", "pl", "pt", "es", "sv", "uk"]:
	#Issues with Cs
	__chapters = ["ca", "eu", "el", "id", "nl", "fr", "de", "ja", "ko", "es"]

	def __init__(self, language):
		if language == "en":
			complement = ""
		else:
			complement = f"{language}."

		if language == "ko":
			super().__init__(f"http://143.248.135.47/sparql")
		else:
			super().__init__(f"http://{complement}dbpedia.org/sparql")

		self.__wwww_complement = ""
		if language in ["en", "es", "eu", "de", "ko", "ja"]:
			self.__wwww_complement = "www."

	@classmethod
	def getSupportedTags(cls):
		return cls.__db_types.keys()

	@classmethod
	def getDBTypes(cls, ner_type):
		return cls.__db_types[ner_type]

	@classmethod
	def getAvailableChapters(cls):
		return cls.__chapters

	def __generateQueryTypes(self, wd_id, freebase_id, ner_tag):
		if wd_id is not None:
			prefix = f"PREFIX wd: <http://{self.__wwww_complement}wikidata.org/entity/>"
			ask_through = f"?sub owl:sameAs wd:{wd_id} ."
		elif freebase_id is not None:
			prefix = "PREFIX freebase: <http://rdf.freebase.com/ns/>"
			ask_through = f"?sub owl:sameAs freebase:{freebase_id} ."
		else:
			return ""
		search_in = SparqlDBPedia.getDBTypes(ner_tag)
		search_in = ", ".join(search_in)
		query = f"""
					PREFIX owl: <http://www.w3.org/2002/07/owl#>
					PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
					PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
					PREFIX foaf: <http://xmlns.com/foaf/0.1/>
					PREFIX umbel-rc: <http://umbel.org/umbel/rc/>
					PREFIX dbc: <http://dbpedia.org/resource/Category>
					PREFIX dbo: <http://dbpedia.org/ontology/>
					PREFIX yago: <http://dbpedia.org/class/yago/>
					PREFIX dul: <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl>
					PREFIX schema: <http://schema.org/>
					{prefix}
					ASK {{
						?sub a ?type .
						FILTER(?type IN ({search_in}))
						{ask_through}
					}}
				"""
		return query

	def __generateQueryExist(self, wd_id, freebase_id):
		if wd_id is not None and freebase_id is not None:
			query = f"""
						PREFIX owl: <http://www.w3.org/2002/07/owl#>
						PREFIX wd: <http://www.wikidata.org/entity/>
						PREFIX freebase: <http://rdf.freebase.com/ns/>
						SELECT DISTINCT ?wikidata_id ?freebase_id
						{{
							{{
								?freebase_id owl:sameAs freebase:{freebase_id} .
								OPTIONAL{{
									?wikidata_id owl:sameAs wd:{wd_id}.
								}}
							}}
							UNION
							{{
								?wikidata_id owl:sameAs wd:{wd_id}.
								OPTIONAL{{
									?freebase_id owl:sameAs freebase:{freebase_id} .
								}}
							}}
						}}
			"""
		else:
			query = f"""
									PREFIX owl: <http://www.w3.org/2002/07/owl#>
									PREFIX wd: <http://www.wikidata.org/entity/>
									SELECT DISTINCT ?wikidata_id
									{{
										?wikidata_id owl:sameAs wd:{wd_id}.
									}}
						"""
		return query

	def __searchExists(self, wd_id, freebase_id):
		query = self.__generateQueryExist(wd_id, freebase_id)
		super().verifyQueryTiming()
		super().setQuery(query)
		results = super().executeQuery()
		if results is not None and len(results["results"]["bindings"]) > 0:
			result = results["results"]["bindings"][0]
			if "wikidata_id" not in result:
				wd_id = None
			if "freebase_id" not in result:
				freebase_id = None
		else:
			wd_id = None
			freebase_id = None
		return wd_id, freebase_id

	def search(self, wd_id, freebase_id, ner_tags):
		wd_id, freebase_id = self.__searchExists(wd_id, freebase_id)
		reply = None
		if wd_id is not None or freebase_id is not None:
			query = self.__generateQueryTypes(wd_id, freebase_id, ner_tags)
			if query == "":
				return None
			super().verifyQueryTiming()
			super().setQuery(query)
			results = super().executeQuery()
			if results is not None:
				reply = results["boolean"]
		return reply
