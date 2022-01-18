# Post-processing filter for (Named) Entity Linking

This program was created for filtering entity linking candidates and reorder them based on heuristics and data coming from DBpedia in most cases. The filter tries to delete improbable candidates, such as disambiguation pages or people born after the publication of the document (if dates are available). It can improve the global performance of an Entity Linking system.

# Where it has been used?

This filter been used in diverse pubications:

* [MELHISSA: a multilingual entity linking architecture for historical press articles](https://doi.org/10.1007/s00799-021-00319-6)

* [Robust Named Entity Recognition and Linking on Historical Multilingual Documents](http://ceur-ws.org/Vol-2696/paper_171.pdf)

* [Exploratory Analysis of News Sentiment Using Subgroup Discovery](https://www.aclweb.org/anthology/2021.bsnlp-1.7/)

* [Entity Linking for Historical Documents: Challenges and Solutions](https://link.springer.com/chapter/10.1007/978-3-030-64452-9_19)

	The current version is the one used in our latest publication _MELHISSA: a multilingual entity linking architecture for historical press articles_. For previous versions, please visit the [old_versions](https://github.com/EMBEDDIA/NEL_Filter/tree/old_versions) branch or you can download  directly the files from [here](https://github.com/EMBEDDIA/NEL_Filter/releases/tag/EMBEDDIA_D2.7). 

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
@Article{LinharesPontes2021,
	author={Linhares Pontes, Elvys
	and Cabrera-Diego, Luis Adrián
	and Moreno, Jose G.
	and Boros, Emanuela
	and Hamdi, Ahmed
	and Doucet, Antoine
	and Sidere, Nicolas
	and Coustaty, Mickaël},
	title={MELHISSA: a multilingual entity linking architecture for historical press articles},
	journal={International Journal on Digital Libraries},
	year={2021},
	month={Nov},
	day={29},
	issn={1432-1300},
	doi={10.1007/s00799-021-00319-6},
	url={https://doi.org/10.1007/s00799-021-00319-6}
}
```

If you use the Weighted-Levenshtein and you use the weights provided in the code, please cite as well:

```
@Inproceedings{8791206,
  author={Nguyen, Thi-Tuyet-Hai and Jatowt, Adam and Coustaty, Mickael and Nguyen, Nhu-Van and Doucet, Antoine},
  booktitle={2019 ACM/IEEE Joint Conference on Digital Libraries (JCDL)}, 
  title={Deep Statistical Analysis of OCR Errors for Effective Post-OCR Processing}, 
  year={2019},
  volume={},
  number={},
  pages={29-38},
  doi={10.1109/JCDL.2019.00015}}

```

# DBpedia Chapters

Some of the DBpedia chapters have become offline during 2020-2021, and we do not know if they will come online again. Thus, there might be some issues in specific configurations. This version should be more robust if a chapter becomes offile.

# Cached data

We provide the cached data that was used for the latest publication. The use of a cache decreases the number of queries to DBpedia and WikiData, and therefore increases the processing speed.

# Dependencies

This project has been tested with Python 3.8. The requirements can be found in `requirements.txt` and can be installed using `pip`.

# Parent projects

This work is is result of the European Union H2020 Project [Embeddia](http://embeddia.eu/) and [NewsEye](https://www.newseye.eu/). Embeddia is a project that creates NLP tools that focuses on European under-represented languages and that has for objective to improve the accessibility of these tools to the general public and to media enterprises. Visit [Embeddia's Github](https://github.com/orgs/EMBEDDIA/) to discover more NLP tools and models created within this project. NewsEye is a project that develops methods and tools for digital humanities that can enhance the access to historical newspapers to a wide range of users. Visit [NewsEye's Github](https://github.com/newseye) to discover the range of tools developed for the digital humanities. 

