#!python3
import os
import json
from pymongo import MongoClient
from py2neo import *

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

class videorel:
	def init_db(self):
		files = os.listdir(os.getcwd() + '/database_api/video_info/');

		authenticate("localhost:7474", "YourTube", "pass")
		graph = Graph();

		data = [];

		for f in files:
			data_file = open(os.getcwd() + '/database_api/video_info/' + f);
			data.append(json.load(data_file));
			data_file.close();

		graph.run("MATCH (v) DETACH DELETE v");
		ids = [];
		data = data[0:50];
		for i in range(0,len(data)):
			d = data[i];
			rv = graph.run("CREATE (v:video { commentCount:" + str(d['videoInfo']['statistics']['commentCount']) + ", viewCount:" + str(d['videoInfo']['statistics']['viewCount']) + ", favoriteCount:" +  str(d['videoInfo']['statistics']['favoriteCount']) + ", dislikeCount:" + str(d['videoInfo']['statistics']['dislikeCount']) + ", likeCount:" + d['videoInfo']['statistics']['likeCount'] + "}) RETURN ID(v);" );
			x = 12;
			for record in rv:
				x = record;
			ids.append(x[u'ID(v)']);
			print i;


		for i in range(0,len(data)-1):
			for j in range(0,len(data)):
				if i != j:
					same_channel = data[i]['videoInfo']['snippet']['channelId'] == data[j]['videoInfo']['snippet']['channelId'];
					
					percentage_tag_match = 0

					if 'tags' in data[i]['videoInfo']['snippet'].keys() and 'tags' in data[j]['videoInfo']['snippet'].keys():
						tagsi = data[i]['videoInfo']['snippet']['tags'];
						tagsj = data[j]['videoInfo']['snippet']['tags'];
						[x.lower() for x in tagsi];
						[x.lower() for x in tagsj];
						common_tags = len(set(tagsi).intersection(set(tagsj)));
						percentage_tag_match = float(common_tags)/len(set(tagsi));


					desci = data[i]['videoInfo']['snippet']['description'].split();
					descj = data[j]['videoInfo']['snippet']['description'].split();
					[x.lower() for x in desci];
					[x.lower() for x in descj];

					common_desc = len(set(desci).intersection(set(descj)));
					percentage_desc_match = 0.0;
					
					if (len(set(desci)) > 0):
						percentage_desc_match = float(common_desc)/len(set(desci));

					if same_channel:
						same_channel = 1;
					else:
						same_channel = 0;

					weightage = 100*(same_channel + percentage_desc_match + 2*percentage_tag_match);
					# print(weightage, " ", percentage_desc_match, " ", common_desc);
					if (weightage > 0):
						graph.run("MATCH (v1:video), (v2:video) WHERE ID(v1) = " + str(ids[i]) + " AND ID(v2) = " + str(ids[j]) + " CREATE (v1)-[r2:WEIGHT {weight:" + str(weightage) + "}]->(v2);");

					# print i," ",j;

