class WikiDataEntry:

	def __init__(self):
		self.__label = None
		self.__alt_labels = []
		self.__year = None
		self.__freebase = None
		self.__disambiguation = False

	def setLabel(self, label):
		self.__label = label

	def getLabel(self):
		return self.__label

	def addAltLabels(self, alt_label):
		self.__alt_labels.append(alt_label)

	def getAltLabels(self):
		return self.__alt_labels

	def setYear(self, year):
		self.__year = year

	def getYear(self):
		return self.__year

	def setFreebaseID(self, freebase_id):
		self.__freebase = freebase_id

	def getFreebaseID(self):
		return self.__freebase

	def setDisambiguation(self):
		self.__disambiguation = True

	def getDisambiguation(self):
		return self.__disambiguation
