from database.api import *
from pandas import DataFrame

import json

class Recommendations(object):
	""" Provide recommendations for a given videoid. Requires info about the
	user currently logged in. """
	""" 1. 15 nearest neighbours in graph.
		2. Filter by user history tags.
		*3*. Use user likes/dislikes.
	"""
	def __init__(self):
		self.userdb = UserInfoDB()
		self.videoinfo = VideoInfo()
		self.userhistory = HistoryTags()
		self.graph = VideosGraph()

	def nearest_neighbours(self, videoid, k=15):
		""" Return a dataframe of records of with columns (videoid, weight). """
		r = self.graph.get_neighbours(videoid,k)
		records = DataFrame(self.graph.get_neighbours(videoid,k).data())
		return records

	def userhistory(self, username, records):
		""" Sort the records (DataFrame) based on user history. """
		data = self.userhistory.get_tags(username)
		tags = [data['tags'][i]['tag'] for i in range(0,len(data))]
		count = [data['tags'][i]['count'] for i in range(0,len(data))]
		hashtable = dict()
		for i in range(0,len(tags)):
			hashtable[tags[i]] = count[i]
		weight = 0
		for i in range(0, len(records)):
			videotags = self.videoinfo.get_tags(records.Neighbor[i])
			[x.lower() for x in videotags]
			common_tags = set(tags).intersection(set(videotags));
			for t in common_tags:
				weight += hashtable[common_tags[i]]
			percentage_tag_match = float(len(common_tags))/len(set(videotags));
			# Update weight of record now.
			records.Similarity[i] += percentage_tag_match*100 + weight

		records = records.sort_values('Similarity', ascending=False)
		return records
