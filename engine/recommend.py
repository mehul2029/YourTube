from database.api import *
from pandas import DataFrame

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
		records = DataFrame(self.graph.get_neighbours(videoid,k).data())
		return records

	def userhistory(self, username, records):
		""" Sort the records (DataFrame) based on user history. """
		usertags = self.userhistory.get_tags(username)
		[x.lower() for x in usertags]
		for i in range(0, len(records)):
			videotags = self.videoinfo.get_tags(records.Neighbor[i])
			[x.lower() for x in videotags]
			common_tags = len(set(usertags).intersection(set(videotags)));
			percentage_tag_match = float(common_tags)/len(set(videotags));
			# Update weight of record now.
			records.Similarity[i] += percentage_tag_match*100

		records = records.sort_values('Similarity', ascending=False)
		return records
