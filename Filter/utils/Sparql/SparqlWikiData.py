import regex
import time
import logging

from Final_Journal.utils.WikiDataEntry import WikiDataEntry
from Final_Journal.utils.Sparql.SparqlObject import SparqlObject


class SparqlWikiData(SparqlObject):

	def __init__(self):
		super().__init__("https://query.wikidata.org/sparql")

	def __generateQuery(self, language, wd_id, first_language):
		additional_information = ""
		select_info = "?widLabel ?altLabel"
		if first_language:
			additional_information = """
				OPTIONAL{
					?wid wdt:P31 ?instanceOf .
					BIND (IF(?instanceOf = wd:Q4167410, "true", "false") AS ?disambP)
					BIND (IF(?instanceOf = wd:Q22808320, "true", "false") AS ?disambH)
				}
				OPTIONAL{
                	?wid p:P569 ?dob_s.
                	?dob_s ps:P569 ?dob.
				}
				OPTIONAL{
					?wid p:P571 ?inception_s .
                	?inception_s ps:P571 ?inception.
                }
				OPTIONAL{
					?wid p:P577 ?publication_s .
                	?publication_s ps:P577 ?publication .
				}
				OPTIONAL{
					?wid p:P729 ?service_s .
                	?service_s ps:P729 ?service .
				}
				OPTIONAL{
					?wid p:P1191 ?performance_s .
                	?performance_s ps:P1191 ?performance .
				}
				OPTIONAL{
					?wid p:P575 ?discovery_s .
                	?discovery_s ps:P575 ?discovery .
				}
				OPTIONAL{
					?wid p:P1619 ?opening_s .
                	?opening_s ps:P1619 ?opening .
				}
			"""
			select_info = "?widLabel ?disambP ?disambH ?dob ?inception ?publication ?service ?performance ?discovery ?opening ?freebase ?altLabel"

		query = f"""
			SELECT {select_info}
			WHERE
			{{
				BIND(wd:{wd_id} AS ?wid)
				{additional_information}
				OPTIONAL{{
					?wid skos:altLabel ?altLabel.
					filter(lang(?altLabel) = '{language}')
				}}
				?wid rdfs:label ?widLabel.
					filter(lang(?widLabel) = '{language}')

				SERVICE wikibase:label {{ bd:serviceParam wikibase:language "'{language}', [AUTO_LANGUAGE]". }}
			}}
			GROUP BY {select_info}
		"""
		return query

	def __generateQueryRedirects(self, wd_id):
		query = f"""
			PREFIX owl: <http://www.w3.org/2002/07/owl#>
			SELECT ?redirects
			WHERE
			{{
				BIND(wd:{wd_id} AS ?wid)
				OPTIONAL{{
					?wid owl:sameAs ?redirects
				}}
			}}
		"""
		return query

	def searchRedirects(self, wd_id):
		query = self.__generateQueryRedirects(wd_id)
		super().verifyQueryTiming()
		super().setQuery(query)
		results = super().executeQuery()
		redirects_to = None
		if len(results["results"]["bindings"]) == 1:
			binding = results["results"]["bindings"][0]
			if "redirects" in binding:
				redirects_to = binding["redirects"]["value"]
				redirects_to = regex.search("entity/(Q.+)", redirects_to)
				if redirects_to is not None:
					redirects_to = redirects_to.group(1)
		return redirects_to

	def search(self, language, wd_id, first_language):
		query = self.__generateQuery(language, wd_id, first_language)
		super().verifyQueryTiming()
		super().setQuery(query)
		try_counter = 0
		try_again = True
		entry = None
		while try_again:
			try_again = False
			results = super().executeQuery()
			if results is None:
				if try_counter == 1:
					raise Exception("Unknown error while querying Wikidata")
				else:
					try_again = True
					try_counter += 1
					logging.error("Error while querying Wikidata, waiting 60s")
					time.sleep(60)
			else:
				entry = self.__processResults(results)
		return entry

	def __processYears(self, value):
		year = regex.search("^\d\d\d\d", value)
		if year is None:
			year = 0
		else:
			year = int(year[0])
		return year

	def __processResults(self, results):
		year_set = set()
		disambiguation_set = set()
		freebase_id_set = set()
		label_set = set()
		alt_labels_set = set()
		if len(results["results"]["bindings"]) == 0:
			entry = None
		else:
			for binding in results["results"]["bindings"]:
				if "dob" in binding:
					year_set.add(self.__processYears(binding["dob"]["value"]))
				if "inception" in binding:
					year_set.add(self.__processYears(binding["inception"]["value"]))
				if "publication" in binding:
					year_set.add(self.__processYears(binding["publication"]["value"]))
				if "service" in binding:
					year_set.add(self.__processYears(binding["service"]["value"]))
				if "performance" in binding:
					year_set.add(self.__processYears(binding["performance"]["value"]))
				if "discovery" in binding:
					year_set.add(self.__processYears(binding["discovery"]["value"]))
				if "opening" in binding:
					year_set.add(self.__processYears(binding["opening"]["value"]))
				if "disambP" in binding:
					disambiguation_page = binding["disambP"]["value"]
					if disambiguation_page == "true":
						disambiguation_set.add(True)
					else:
						disambiguation_set.add(False)
				if "disambH" in binding:
					disambiguation_page = binding["disambH"]["value"]
					if disambiguation_page == "true":
						disambiguation_set.add(True)
					else:
						disambiguation_set.add(False)
				if "freebase" in binding:
					free_id = regex.sub("^/", "", binding["freebase"]["value"])
					free_id = regex.sub("/", ".", free_id)
					freebase_id_set.add(free_id)
				if "widLabel" in binding:
					label_set.add(binding["widLabel"]["value"])
				if "altLabel" in binding:
					alt_labels_set.add(binding["altLabel"]["value"])

			year_set = list(year_set)
			freebase_id_set = list(freebase_id_set)
			label_set = list(label_set)

			entry = WikiDataEntry()
			if len(label_set) > 1:
				raise Exception("Number of labels is greater than 1")
			elif len(label_set) > 0:
				entry.setLabel(label_set[0])

			for alt_label in alt_labels_set:
				entry.addAltLabels(alt_label)

			if len(year_set) > 0:
				min_year = year_set.pop(0)
				for year in year_set:
					if year < min_year:
						min_year = year
				entry.setYear(min_year)

			if len(disambiguation_set) > 0:
				for disambiguation in disambiguation_set:
					if disambiguation is True:
						entry.setDisambiguation()

			if len(freebase_id_set) > 1:
				raise Exception("Number of freebase ids is greater than 1")
			elif len(freebase_id_set) > 0:
				entry.setFreebaseID(freebase_id_set[0])

		return entry
