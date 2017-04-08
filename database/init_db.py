#!python3
import os
import json
from pymongo import MongoClient

class videoinfo:
	def init_db(self):
		client = MongoClient()
		db = client.YourTube
		path = os.getcwd() + '/database_api/video_info/'

		for filename in os.listdir(path):
			with open(path + filename) as data_file: 
				data = json.load(data_file)
				data['videoInfo']['statistics']['likeCount'] = int(data['videoInfo']['statistics']['likeCount'])
				post_id = db.video_info.insert_one(data).inserted_id

		print("Video Info Database Set")
