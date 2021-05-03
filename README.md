# Post-processing filter for Entity Linking

This filter been used in diverse pubications. However, for each publication, we have modified slightly the code to improve the performance on the corpora analyzed. Later, we will make available an improved version of the filter once the related work has been published.

### Robust Named Entity Recognition and Linking on Historical Multilingual Documents

### Exploratory Analysis of News Sentiment Using Subgroup Discovery

### Entity Linking for Historical Documents: Challenges and Solutions

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
