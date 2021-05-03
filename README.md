# Post-processing filter for Entity Linking

This program was created for filtering entity linking candidates and reorder them based on heuristics and data coming from DBpedia in most cases. The filter tries to delete illogical candidates, such as disambiguation pages or people born after the publication of the document (if dates are available). It can improve the global performance of an Entity Linking system.

# Where has been used?

This filter been used in diverse pubications. However, for each publication, we have modified slightly the code to improve the performance on the corpora analyzed. Later, we will make available an improved version of the filter once the related work has been published.

* [Robust Named Entity Recognition and Linking on Historical Multilingual Documents](http://ceur-ws.org/Vol-2696/paper_171.pdf) (CLEF-HIPE): Two filters are provided, A and B. The former was used for RUN 1 and RUN 2, while the latter was used for RUN 3. The main difference is that filter B uses information from Wikidata. Wikidata helps us to retrieve some date of births that couldn't be found in DBpedia and determine whether the entry was a disambiguation page. Both filters use the format used for CLEF-HIPE 2020.

* [Exploratory Analysis of News Sentiment Using Subgroup Discovery] (https://www.aclweb.org/anthology/2021.bsnlp-1.7/) (BSNLP): This version is based on CLEF-HIPE_A of the filter and introduced some improvements in the code, such as the liberty of choosing the columns in which the NER and EL data are found. We do not recommend to use this code.

* [Entity Linking for Historical Documents: Challenges and Solutions] (https://link.springer.com/chapter/10.1007/978-3-030-64452-9_19) (ICADL): This is the current version of the filter. It contains the innovations introduced for BSNLP, fixes multiples issues in the logic behind and add the capacity of querying DBpedia Chapters.

# Input format

The code use a column-based format, in which it is necessary to have data regarding the tokens, named entity and entity linking. It has been created for the format used in CLEF-HIPE-2020:

```
TOKEN	NE-COARSE-LIT	NE-COARSE-METO	NE-FINE-LIT	NE-FINE-METO	NE-FINE-COMP	NE-NESTED	NEL-LIT	NEL-METO
# language = en
# newspaper = sn83030483
# date = 1790-01-02
# document_id = sn83030483-1790-01-02-a-i0004
FROM	O	O	O	O	O	_	_	_
A	O	O	O	O	O	_	_	_
VIRGINIA	B-loc	O	B-loc	O	O	_	Q1370|Q1070529|NIL|Q16155633|Q4112016	_
PAPER	O	O	O	O	O	_	_	_
.	O	O	O	O	O	_	_	_
```

We use the comment `date =` to extract the publication date.

Although in the last version (ICADL), it is possible to indicate the columns in which this data is available, and separators and comments, we haven't tested it with other formats.

Furthermore, the filter uses the data provided by the NER tags to process the candidates. Currently, it only supports NER tags encoded with a IOB format.

# Citing

Please use this publication for citing this work:
```
@inproceedings{linhares_pontes_entity_2020,
	address = {Kyoto, Japan},
	title = {Entity {Linking} for {Historical} {Documents}: {Challenges} and {Solutions}},
	isbn = {978-3-030-64451-2},
	doi = {10.1007/978-3-030-64452-9_19},
	booktitle = {Proceedings of the 22nd {International} {Conference} on {Asia}-{Pacific} {Digital} {Libraries} ({ICADL} 2020)},
	publisher = {Springer International Publishing},
	author = {Linhares Pontes, Elvys and Cabrera-Diego, Luis Adrián and Moreno, Jose G. and Boros, Emanuela and Hamdi, Ahmed and Sidère, Nicolas and Coustaty, Mickaël and Doucet, Antoine},
	editor = {Ishita, Emi and Pang, Natalie Lee San and Zhou, Lihong},
	year = {2020},
	pages = {215--231}
}
```

# FuzzyWuzzy vs RapidFuzz

The original implementation of the code used [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy). However, as this library is not compatible with the MIT license, we migrated the library to [RapidFuzz](https://github.com/maxbachmann/RapidFuzz/). RapidFuzz implements the same ideas of FuzzyWuzzy and fixes some the issues. Although there shouldn't be great changes on its performance, it is possible to return to the original library by modifing the source code.
