import os
import logging
from pathlib import Path

from Filter.Filtering import FilteringNEL

root_path = "/home/user/data/"
cache_saving_path = f"./data"
collection = "HIPE"
filter_type = 18
if not os.path.exists(f"{root_path}/mel+baseline_filter{filter_type}"):
	os.mkdir(f"{root_path}/mel+baseline_filter{filter_type}")

logging.basicConfig(filename=f"{root_path}/logs/{collection}_filter{filter_type}.log", level=logging.INFO)

if filter_type == 2:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0,
					   no_candidates=5, filter=True, skip_header=True)
elif filter_type == 4: #Old 3
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["loc", "org", "per", "prod"],
					   notFound_position="afterTop", no_candidates=5, filter=True, skip_header=True)
elif filter_type == 5: #Old 4
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0,
					   notFound_position="afterTop", no_candidates=5, filter=True, skip_header=True)
elif filter_type == 3: #Old 5
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["per"],
					   no_candidates=5, filter=True, skip_header=True)
elif filter_type == 6:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["per"],
					   notFound_position="afterTop", no_candidates=5, filter=True, skip_header=True)
elif filter_type == 7:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["loc", "org", "per", "prod"],
					   tokens_comparison=False, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 8:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0,
					   tokens_comparison=False, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 10: #Old 9
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["loc", "org", "per", "prod"],
					   notFound_position="afterTop", tokens_comparison=False, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 11: #Old 10
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0,
					   notFound_position="afterTop", tokens_comparison=False, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 9: #Old 11
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["per"],
					   tokens_comparison=False, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 12:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["per"],
					   notFound_position="afterTop", tokens_comparison=False, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 13:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["loc", "org", "per", "prod"],
				 wlev=True, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 14:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0,
				 wlev=True, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 16: #Old 15
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["loc", "org", "per", "prod"],
				 notFound_position="afterTop", wlev=True, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 17: #Old 16
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0,
				 notFound_position="afterTop", wlev=True, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 15: #Old 17
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["per"],
				 wlev=True, no_candidates=5, filter=True, skip_header=True)
elif filter_type == 18:
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["per"],
				 notFound_position="afterTop", wlev=True, no_candidates=5, filter=True, skip_header=True)
else: #Filter1
	nel = FilteringNEL("#", cache_saving_path, lit_col=1, meto_col=None, wd_col=7, tokens_col=0, filter_by_date=["loc", "org", "per", "prod"],
					   no_candidates=5, filter=True, skip_header=True)


if collection == "HIPE":
	for lang in ["fr", "de", "en"]:
		for input_file in Path(f"{root_path}/mel+baseline_input/").glob(f"HIPE-data-v1.3-test-{lang}-*.tsv"):
			logging.info(f"Processing: {input_file}")
			output_file = os.path.splitext(os.path.basename(input_file))[0]
			output_file = f"{root_path}/mel+baseline_filter{filter_type}/{output_file}_filter{filter_type}.tsv"
			nel.readFile(lang, input_file, output_file, collection_format=collection, languageToCache=[lang])

elif collection == "NewsEye":
	for lang in ["de", "fr", "sv", "fi"]:
		for input_file in Path(f"{root_path}/mel+baseline_input/").glob(f"{lang}-test-*.tsv"):
			logging.info(f"Processing: {input_file}")
			output_file = os.path.splitext(os.path.basename(input_file))[0]
			output_file = f"{root_path}/mel+baseline_filter{filter_type}/{output_file}_filter{filter_type}.tsv"
			nel.readFile(lang, input_file, output_file, collection_format=collection, languageToCache=[lang])