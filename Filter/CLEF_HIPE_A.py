#This was used for RUN1 and RUN2 in CLEF HIPE 2020
import time

from SPARQLWrapper import SPARQLWrapper, JSON
from stop_words import get_stop_words
import regex
#Change the rapidfuzz for fuzzywuzzy if it is needed the original implementation
from rapidfuzz import fuzz
import unidecode


class FilteringNEL:

    def __init__(self, lang, input_file_path, output_file_path, comment_token, freeling=False, sep="|"):
        self.__db_types = {
            "loc": ["dbo:Location", "dbo:Settlement", "dbo:Region", "dbo:Building", "dbo:Village",
                    "umbel-rc:Country", "yago:YagoGeoEntity"],
            "org": ["dbo:Organisation", "umbel-rc:Business", "dbc:Supraorganizations", "yago:YagoGeoEntity"],
            "pers": ["foaf:Person", "dbo:Person", "dbo:Agent", "dul:SocialPerson"],
            "prod": ["dbo:Work", "dbo:Newspaper", "umbel-rc:Business"]
        }
        self.__sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        self.__lang = lang
        self.__stop_words_list = get_stop_words(lang)
        self.__input_file_path = input_file_path
        self.__output_file_path = output_file_path
        self.__comment_token = comment_token
        self.__output_file = None
        self.__last_query_time = time.time()
        self.__last_query_counter = 0
        self.__news_date = 3000
        self.__freeling = freeling
        self.__sep=sep

    def verifyQueryTiming(self):
        current_time = time.time()
        if 0 >= current_time - self.__last_query_time > 1:
            self.__last_query_counter += 1
            if self.__last_query_counter >= 50:
                time.sleep(1)
        else:
            self.__last_query_counter = 0
            self.__last_query_time = current_time

    def askExistsQuery(self, wd_id):
        query_base = f"""
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                    PREFIX wd: <http://www.wikidata.org/entity/>
                    ASK {{
                        ?sub owl:sameAs wd:{wd_id} .
                    }}
                """
        self.verifyQueryTiming()
        self.__sparql.setQuery(query_base)
        self.__sparql.setReturnFormat(JSON)
        result = self.__sparql.query().convert()
        return result["boolean"]

    def createQuery(self, db_types, wd_id):
        sorting = ""
        sort_by = []
        select_elements = ["?sub", "?lbl"]
        query_dob = ""
        search_in = []
        for db_type in db_types:
            search_in += self.__db_types[db_type]
            if db_type == "pers":
                query_dob = f"""
                   OPTIONAL{{
                       ?sub dbo:birthDate ?dob
                       BIND(REPLACE(?dob, "-.+$", "") AS ?year)
                   }}
                """
                select_elements.append("?year")
        search_in = set(search_in)
        search_in = ", ".join(search_in)

        if len(sort_by) > 0:
            sort_by = " ".join(sort_by)
            sorting = f"ORDER BY {sort_by}"
        select = " ".join(select_elements)

        query_base = f"""
                    PREFIX owl: <http://www.w3.org/2002/07/owl#>
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
                    PREFIX wd: <http://www.wikidata.org/entity/>
                    SELECT {select} WHERE {{
                        ?sub a ?type .
                        FILTER(?type IN ({search_in}))
                        ?sub owl:sameAs wd:{wd_id}.
                        ?sub rdfs:label ?lbl .
                        FILTER(langMatches(lang(?lbl), "{self.__lang}"))
                        {query_dob}
                    }}
                    GROUP BY ?sub
                    {sorting}
                """
        return query_base

    def runQuery(self, nel_query, wd_id):
        self.verifyQueryTiming()
        self.__sparql.setQuery(nel_query)
        self.__sparql.setReturnFormat(JSON)
        results = self.__sparql.query().convert()
        parsed_results = {}
        if len(results["results"]["bindings"]) == 0:
            parsed_results[wd_id] = None
            #return None
        else:
            result = results["results"]["bindings"][0]
            if "year" in result:
                year = result["year"]["value"]
                if year == "":
                    year = 0 #This means that the year was negative
                if int(year) > self.__news_date + 10:
                    return None
            parsed_results[wd_id] = result["lbl"]["value"]
        return parsed_results

    def processToken(self, tokens, tags_to_process, wd_ids, shift_to_comment=False, nested=False):
        supported_tags = []
        for tag in tags_to_process:
            if tag in self.__db_types.keys():
                supported_tags.append(tag)
        if len(supported_tags) == 0:
            return "|".join(wd_ids)
        label_keys = []
        tokens_as_string = ""
        comment_keys = []
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
            #tokens_as_string += f"{token} "
            if regex.search("\p{P}|\p{S}", token):
                continue
            token = unidecode.unidecode(token)
            if token.lower() in self.__stop_words_list or len(token) == 1:
                continue
            if token.lower() in ["and", "or"]:
                continue
            if shift_to_comment:
                comment_keys.append(token)
            else:
                label_keys.append(token)

        results = {}
        wd_ids_to_skip = set()
        last_position = []

        if len(label_keys) > 0:
            for wd_id in wd_ids:
                if wd_id in ["_", ""]:
                    wd_ids_to_skip.add(wd_id)
                elif wd_id in ["NIL"]:
                    continue
                elif self.askExistsQuery(wd_id):
                    nel_query = self.createQuery(supported_tags, wd_id)
                    temp_results = self.runQuery(nel_query, wd_id)
                    if temp_results is None:                    #We must skip this person
                        wd_ids_to_skip.add(wd_id)
                    else:
                        if temp_results[wd_id] is None:
                            last_position.append(wd_id)
                        results.update(temp_results)
        return self.processResults(results, wd_ids_to_skip, last_position, wd_ids, tokens_as_string)

    def processResults(self, results, wd_ids_to_skip, last_position, wd_ids, tokens_as_string):
        #if results is None or len(results) == 0:
        #    return "NIL"
        best_result = "NIL"
        best_distance = 500 #I just consider that the distances should be smaller
        for (key, value) in results.items():
            if value is not None and value != "":
                #distance = editdistance.eval(value.lower(), tokens_as_string.lower())
                distance = 100 - fuzz.WRatio(value.lower(), tokens_as_string.lower())
                if distance < best_distance:
                    best_distance = distance
                    best_result = key
        final_results = []
        catch_nil = False
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
        final_results.insert(0, best_result)
        if best_result == "NIL":
            catch_nil = True
        if not catch_nil:
            while len(final_results) > 4:
                final_results.pop()
            final_results.append("NIL")
        else:
            while len(final_results) > 5:
                final_results.pop()
        return "|".join(final_results)

    def readFile(self):
        self.__output_file = open(self.__output_file_path, "w")
        with open(self.__input_file_path) as input_file:
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
                elif line.startswith(self.__comment_token):
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
                    if columns[1] == "O":
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
                        if columns[1][0] == "B":
                            if len(tokens) > 0:
                                result = self.processToken(tokens, tags_to_process, wd_ids)
                                self.generateNELOutput(rows, result)
                                tokens = []
                                rows = []
                                tag_lit = ""
                                tags_to_process = []
                                wd_ids = []
                            tag_lit = columns[1][2:]
                            tags_to_process.append(tag_lit)
                            wd_ids = columns[7].split(self.__sep)
                        if columns[1][0] == "I" and tag_lit == "": #Just in case the labeling isn't the correct one
                            tag_lit = columns[1][2:]
                            tags_to_process.append(tag_lit)
                            wd_ids = columns[7].split(self.__sep)
                        if columns[2][0] != "O":
                            meto_tag = columns[2][2:]
                            meto_tag = regex.sub("\..+$", "", meto_tag)
                            if meto_tag not in tags_to_process:
                                tags_to_process.append(meto_tag)
                        rows.append(columns)
                        tokens.append(columns[0])
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
                    columns[-3] = result
                    if columns[2] != "O": #For METO
                        columns[-2] = result
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

