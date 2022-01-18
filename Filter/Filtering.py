import os
import regex
from rapidfuzz import fuzz
import logging

from Filter.utils.Cache import Cache, RedirectionCache
from Filter.utils.Sparql.SparqlDBPedia import SparqlDBPedia
from Filter.utils.Sparql.SparqlWikiData import SparqlWikiData
from Filter.utils.WeightedLevenshtein import WeightedLevenshtein


class FilteringNEL:

    def __init__(self, comment_token, cache_saving_path, sep="|", tokens_col=0, lit_col=1, meto_col=None,
				 wd_col=2, no_candidates=1, start_at=0, skip_header=False, filter=True, notFound_position="asBottom",
				 add_inter_NIL=True, add_final_NIL=True, trunk_results="beforeFinalNIL", year_threshold=1,
				 tokens_comparison=True, load_cache=True, filter_by_date=None, wlev=False, check_non_ne=True):

        self.__lang = None
        self.__input_file_path = None
        self.__output_file_path = None
        self.__collection_format = None

        self.__tokens_col = tokens_col
        self.__lit_col = lit_col
        self.__meto_col = meto_col
        self.__wd_col = wd_col

        self.__comment_token = comment_token
        self.__output_file = None
        self.__sep = sep
        self.__no_candidates = no_candidates
        self.__start_at = start_at
        self.__skip_header = skip_header
        self.__filter = filter
        self.__check_non_ne = check_non_ne

        self.__cache = Cache()
        self.__redirection_cache = RedirectionCache()
        self.__languagesToCache = []
        self.__wikidata = SparqlWikiData()
        self.__dbpedia = SparqlDBPedia("en")
        self.__dbpedia_chapters = []
        for language in SparqlDBPedia.getAvailableChapters():
            self.__dbpedia_chapters.append(SparqlDBPedia(language))

        self.__tokens_comparison = tokens_comparison
        self.__notFound_position = notFound_position
        self.__add_inter_NIL = add_inter_NIL
        self.__trunk_results = trunk_results
        self.__add_final_NIL = add_final_NIL
        self.__year_threshold = year_threshold
        self.__filter_by_date = filter_by_date
        self.__cache_saving_file = f"{cache_saving_path}/cache.pkl"
        self.__redirection_saving_file = f"{cache_saving_path}/redirection_cache.pkl"
        if load_cache and os.path.exists(self.__cache_saving_file):
            self.__cache.loadCache(self.__cache_saving_file)
        if load_cache and os.path.exists(self.__redirection_saving_file):
            self.__redirection_cache.loadCache(self.__redirection_saving_file)
        self.__wlev = None
        if wlev:
            self.__wlev = WeightedLevenshtein()

    def __processEntry(self, language, entry, article_year=None, tag=None):
        processed_entry = []
        if self.__filter_by_date is not None:
            if tag in self.__filter_by_date:
                if article_year is not None and entry.getYear() is not None:
                    if entry.getYear() > article_year + self.__year_threshold:
                        processed_entry = None

        if processed_entry is not None:
            processed_entry = [entry.getLabel(language)]
            for altLabel in entry.getAltLabels(language):
                processed_entry.append(altLabel)
        return processed_entry

    def __processToken(self, tokens, tags_to_process, wd_ids, article_year=None):
        results = {}
        top_ids = []
        notFound_ids = []
        tokens_as_string = ""
        disambiguation = False
        if self.__filter:
            supported_tags = []
            for tag in tags_to_process:
                if tag == "pers":
                    tag = "per"
                if tag == "humanprod":
                    tag = "prod"
                if tag in SparqlDBPedia.getSupportedTags():
                    supported_tags.append(tag)
            if len(supported_tags) == 0:
                return "|".join(wd_ids)
            tokens_as_string += " ".join(tokens)
            tokens_as_string = regex.sub("(:?^ | +| $)", "", tokens_as_string)
            original_order = []
            for wd_id in wd_ids:
                if wd_id in ["_", "", "NIL"]:
                    continue
                else:
                    does_redirect = self.__redirection_cache.redirects(wd_id)
                    if does_redirect is not None and does_redirect is True:
                        wd_id = self.__redirection_cache.redirectsTo(wd_id)
                    entry = self.__cache.getEntry(wd_id)
                    # Get data from Wikidata
                    first_language = True
                    if entry.exists():
                        first_language = False
                        if entry.isDisambiguationPage():
                            continue
                    for language in self.__languagesToCache:
                        if not entry.existsInLanguage(language):
                            try:
                                wd_entry = self.__wikidata.search(language, wd_id, first_language)
                                if wd_entry is None:
                                    if first_language:
                                        logging.info(f"Searching a redirection for {wd_id}")
                                        redirects_to = self.__wikidata.searchRedirects(wd_id)
                                        self.__redirection_cache.setRedirection(wd_id, redirects_to)
                                        if redirects_to is not None:
                                            logging.error(f"Redirection for {wd_id} is {redirects_to}")
                                            self.__cache.deleteEntry(wd_id)
                                            wd_id = redirects_to
                                            entry = self.__cache.getEntry(wd_id)
                                            wd_entry = self.__wikidata.search(language, wd_id, first_language)
                                            if wd_entry.getLabel() is None:
                                                logging.error(f"Entry {wd_id} didn't have label in {language}")
                                        else:
                                            logging.error(f"Redirection for {wd_id} not found")
                                    else:
                                        logging.error(f"Entry {wd_id} didn't have label in {language}")
                                elif wd_entry.getLabel() is None:
                                    logging.error(f"Entry {wd_id} didn't have label in {language}")
                                entry.addLanguage(language, wd_entry)
                                if entry.isDisambiguationPage():
                                    disambiguation = True
                                    break
                            except Exception as e:
                                logging.error(f"Issue in Wikidata part: {e}")
                                self.__cache.saveCache(self.__cache_saving_file)
                                self.__redirection_cache.saveCache(self.__redirection_saving_file)
                                raise e
                        first_language = False
                    if disambiguation:
                        continue
                    # Get data from DBpedia
                    for tag in supported_tags:
                        if entry.foundInDBpedia() is None or (
                                entry.isAssociatedTo(tag) is None and entry.foundInDBpedia() is True):
                            try:
                                association = self.__dbpedia.search(wd_id, entry.getFreebase(), tag)
                                best_association = association
                                if association is None or association is False:
                                    # logging.info(f"Searching an association for {wd_id} regarding {tag} in DBpedia Chapters")
                                    for dbpedia_chapter in self.__dbpedia_chapters:
                                        association = dbpedia_chapter.search(wd_id, entry.getFreebase(), tag)
                                        if association is not None:
                                            best_association = association
                                            if association is True:
                                                logging.info(
                                                    f"Found association of {wd_id} for {tag} at {dbpedia_chapter.getEntryPoint()}")
                                                break
                                if best_association is not None:
                                    entry.setAssociationTo(tag, best_association)
                                    entry.setFoundInDBpedia(True)
                                else:
                                    logging.info(f"{wd_id} not found in either DBpedia or DBpedia Chapters")
                                    entry.setFoundInDBpedia(False)

                            except Exception as e:
                                logging.error(f"Issue in DBpedia part:{e}")
                                self.__cache.saveCache(self.__cache_saving_file)
                                self.__redirection_cache.saveCache(self.__redirection_saving_file)
                                raise e
                        processed_entry = self.__processEntry(self.__lang, entry, article_year=article_year, tag=tag)
                        if processed_entry is not None:
                            results[wd_id] = processed_entry
                            if not entry.foundInDBpedia():
                                notFound_ids.append(wd_id)
                            elif entry.isAssociatedTo(tag):
                                top_ids.append(wd_id)
                    original_order.append(wd_id)
        else:
            for wd_id in wd_ids:
                if wd_id in ["_", "", "NIL"]:
                    continue
                top_ids.append(wd_id)
            original_order = wd_ids
        try:
            final_results = self.__processResults(results, top_ids, notFound_ids, original_order, tokens_as_string)
        except Exception as e:
            logging.error(f"Error while processing results {e}")
            self.__cache.saveCache(self.__cache_saving_file)
            self.__redirection_cache.saveCache(self.__redirection_saving_file)
            raise e
        return final_results

    def __processResults(self, results, top_ids, notFound_ids, original_order, tokens_as_string):
        final_results = []
        distance_results = {}
        top_results = []
        notFound_results = []
        bottom_results = []
        added_NIL = False
        if self.__filter:
            if self.__tokens_comparison:
                for (wd_id, labels) in results.items():
                    if labels is None:
                        continue
                    best_local_distance = float("inf")
                    for label in labels:
                        distance = float("inf")
                        if label is None:
                            logging.error(f"{wd_id} label is None")
                        elif label == "":
                            logging.error(f"{wd_id} is empty")
                        elif tokens_as_string is None:
                            logging.error(f"Tokens as string is None")
                        elif tokens_as_string == "":
                            logging.error(f"Tokens as string is empty")
                        elif self.__wlev is not None:
                            distance = self.__wlev.calculate(label, tokens_as_string)
                        else:
                            # Automatically does the lowercasing of the strings
                            distance = 100 - fuzz.WRatio(label, tokens_as_string)

                        if best_local_distance > distance:
                            best_local_distance = distance
                    distance_results[wd_id] = best_local_distance
                # We break ties with the original order
                for wd_id, _ in sorted(distance_results.items(), key=lambda x: (x[1], original_order.index(x[0]))):
                    if wd_id in top_ids:
                        top_results.append(wd_id)
                    elif wd_id in notFound_ids:
                        if self.__notFound_position == "asBottom":
                            bottom_results.append(wd_id)
                        else:
                            notFound_results.append(wd_id)
                    else:
                        bottom_results.append(wd_id)
            else:
                for wd_id, _ in sorted(results.items(), key=lambda x: (original_order.index(x[0]))):
                    if wd_id in top_ids:
                        top_results.append(wd_id)
                    elif wd_id in notFound_ids:
                        if self.__notFound_position == "asBottom":
                            bottom_results.append(wd_id)
                        else:
                            notFound_results.append(wd_id)
                    else:
                        bottom_results.append(wd_id)

            for wd_id in top_results:
                final_results.append(wd_id)

            if self.__notFound_position == "afterTop":
                for wd_id in notFound_results:
                    final_results.append(wd_id)
            if self.__add_inter_NIL:
                final_results.append("NIL")
                if len(final_results) <= self.__no_candidates:
                    added_NIL = True
            if self.__notFound_position == "afterInterNIL":
                for wd_id in notFound_results:
                    final_results.append(wd_id)

            for wd_id in bottom_results:
                final_results.append(wd_id)

            if self.__notFound_position == "afterBottom":
                for wd_id in notFound_results:
                    final_results.append(wd_id)
        else:
            final_results = top_ids

        if self.__trunk_results == "beforeFinalNIL":
            modifier = 0
            if not added_NIL:
                modifier = 1
            while len(final_results) > self.__no_candidates - modifier:
                final_results.pop()
        if self.__add_final_NIL and not added_NIL:
            final_results.append("NIL")
        if self.__trunk_results == "after":
            while len(final_results) > self.__no_candidates:
                final_results.pop()
        return "|".join(final_results)

    def readFile(self, lang, input_file_path, output_file_path, collection_format=None, languageToCache=None):
        self.__lang = lang
        self.__input_file_path = input_file_path
        self.__output_file_path = output_file_path
        self.__collection_format = collection_format
        if languageToCache is not None:
            self.__languagesToCache = languageToCache

        if self.__start_at == 0:
            self.__output_file = open(self.__output_file_path, "w")
        else:
            self.__output_file = open(self.__output_file_path, "a")
        skip_lines = 0
        with open(self.__input_file_path) as input_file:
            line_counter = 0
            if self.__start_at > 0:
                while self.__start_at > skip_lines:
                    line = input_file.readline()
                    skip_lines += 1
                    line_counter += 1
            else:
                if self.__skip_header:
                    line = input_file.readline()  # Header
                    line = line.rstrip('\n')
                    self.__printOutput(line)
                    line_counter += 1
                line = input_file.readline()
            tokens = []
            rows = []
            tag_lit = ""
            wd_ids = []
            tags_to_process = []
            article_year = None
            while line:
                line_counter += 1
                line = line.rstrip('\n')
                if line == "":
                    if len(tokens) > 0:
                        result = self.__processToken(tokens, tags_to_process, wd_ids, article_year=article_year)
                        self.__generateNELOutput(rows, result, line_counter)
                        tokens = []
                        rows = []
                        tag_lit = ""
                        tags_to_process = []
                        wd_ids = []
                    self.__printOutput(line)
                elif self.__comment_token is not None and line.startswith(self.__comment_token):
                    if self.__collection_format == "HIPE":
                        if line.startswith("# date = "):
                            article_year = int(regex.search("\d\d\d\d", line)[0])
                    elif self.__collection_format == "NewsEye":
                        if line.startswith("# document_id"):
                            article_year = None
                        elif line.startswith("# -- Newspaper --"):
                            year_pattern = regex.search("-- Issue -- ([^\t]+)\t", line)
                            if year_pattern is not None:
                                year_pattern = year_pattern.group(1)
                                if year_pattern == "NA":
                                    article_year = None
                                elif len(year_pattern) == 10:
                                    article_year = int(regex.search("\d\d\d\d", year_pattern)[0])
                                else:
                                    article_year = int(regex.search("^\d\d\d\d", year_pattern)[0])
                            else:
                                article_year = None

                    if tag_lit == "":
                        self.__printOutput(line)
                    else:
                        rows.append(line)
                else:
                    columns = line.split("\t")
                    print(f"{line}\n")
                    if columns[self.__lit_col] == "O":
                        if len(tokens) > 0:
                            result = self.__processToken(tokens, tags_to_process, wd_ids, article_year=article_year)
                            self.__generateNELOutput(rows, result, line_counter)
                            tokens = []
                            rows = []
                            tag_lit = ""
                            tags_to_process = []
                            wd_ids = []
                        # self.printOutput(line)
                        self.__generateNELOutput([columns], None, line_counter)
                    else:
                        if columns[self.__lit_col][0] == "B":
                            if len(tokens) > 0:
                                result = self.__processToken(tokens, tags_to_process, wd_ids, article_year=article_year)
                                self.__generateNELOutput(rows, result, line_counter)
                                tokens = []
                                rows = []
                                tag_lit = ""
                                tags_to_process = []
                                wd_ids = []
                            tag_lit = columns[self.__lit_col][2:].lower()
                            tags_to_process.append(tag_lit)
                            wd_ids = columns[self.__wd_col].split(self.__sep)
                        if columns[self.__lit_col][
                            0] == "I" and tag_lit == "":  # Just in case the labeling isn't the correct one
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
                result = self.__processToken(tokens, tags_to_process, wd_ids)
                self.__generateNELOutput(rows, result, line_counter)
        self.__output_file.close()
        self.__cache.saveCache(self.__cache_saving_file)
        self.__redirection_cache.saveCache(self.__redirection_saving_file)

    def __printOutput(self, line):
        self.__output_file.write(f"{line}\n")
        self.__output_file.flush()

    def __generateNELOutput(self, rows, result, line_counter):
        for columns in rows:
            if type(columns) is list:
                if result is not None:
                    columns[self.__wd_col] = result
                    if self.__meto_col is not None and columns[self.__meto_col] != "O":  # For METO
                        columns[self.__wd_col + 1] = result
                elif columns[self.__wd_col] != "_" and self.__check_non_ne:
                    logging.info(
                        f"Found non-entity ( {columns[self.__tokens_col]} ) in Line {line_counter} with a link.")
                    columns[self.__wd_col] = "_"
                nel_output = "\t".join(columns)
                self.__printOutput(nel_output)
            else:
                self.__printOutput(columns)
