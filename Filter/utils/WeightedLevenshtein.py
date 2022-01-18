import numpy as np
from weighted_levenshtein import lev


class WeightedLevenshtein:

	def __init__(self):
		scores = {}
		self.__substitute_costs = np.ones((128, 128), dtype=np.float64)
		with open("./data/ocr_char.data", "r", encoding="utf-8") as f:
			for l in f:
				c, mono, per, nla, lc = l.rstrip().split("\t")
				mono, per, nla, lc = mono[1:-1], per[1:-1], nla[1:-1], lc[1:-1]
				scores[c] = {}
				scores[c] = self.__get_values(scores[c], mono)
				scores[c] = self.__get_values(scores[c], per)
				scores[c] = self.__get_values(scores[c], nla)
				scores[c] = self.__get_values(scores[c], lc)

				for ocr in scores[c]:
					self.__substitute_costs[ord(c), ord(ocr)] = 1.0 - scores[c][ocr] / 400.0

		self.__insert_costs = np.ones(128, dtype=np.float64)
		self.__delete_costs = np.ones(128, dtype=np.float64)
		punct_marks = ["'", '"', "-", "_", "\\", "/", ";", ".", ":", "!", "<", ">", "[", "]", "|", "}", "{", "(", ")"]
		for mark in punct_marks:
			self.__delete_costs[ord(mark)] = 0.1
			self.__insert_costs[ord(mark)] = 0.1

	def __get_values(self, scores, data):
		for ocr in data.split(", "):
			char, v = ocr.split(": ")
			v = float(v)
			if char != "@" and char in scores:
				scores[char] += v
			elif char != "@":
				scores[char] = v
		return scores

	def calculate(self, string1, string2):
		string1 = string1.encode('ascii', 'ignore').lower()
		string2 = string2.encode('ascii', 'ignore').lower()
		distance = lev(string1, string2, insert_costs=self.__insert_costs, delete_costs=self.__delete_costs,
					   substitute_costs=self.__substitute_costs)
		return distance
