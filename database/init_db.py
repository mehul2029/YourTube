""" Initialize and populate the Databases. """

#!python3
import os
import json
from pymongo import *
from py2neo import *
from sqlalchemy import *
import _mysql

class Videoinfo(object):
	""" Mongodb DB of video's raw info. """

	def init_db(self):
		""" Initialize a Mongodb database and populate it with raw info of videos.
			Create two indexes:
								1. Text index
								2. Hash Index for id
		"""
		client = MongoClient()
		db = client.YourTube
		path = os.getcwd() + '/database/video_info/'

		try:
			db.video_info.delete_many({})
		except:
			pass

		for filename in os.listdir(path):
			with open(path + filename) as data_file:
				data = json.load(data_file)
				data['videoInfo']['statistics']['likeCount'] = int(data['videoInfo']['statistics']['likeCount'])
				post_id = db.video_info.insert_one(data).inserted_id

		try:
			db.video_info.drop_index("search_index");
		except:
			pass
		# Text Index is created
		db.video_info.create_index(
							[
								("videoInfo.snippet.title", "text"),
								("videoInfo.snippet.description", "text"),
								("videoInfo.snippet.tags", "text")

							],
							name="search_index",
							weights={
							"videoInfo.snippet.title" : 30,
							"videoInfo.snippet.description" : 5,
							"videoInfo.snippet.tags" : 10
							}
						)

		try:
			db.video_info.drop_index("id");
		except:
			pass

		# Hash index is created for `id`
		db.video_info.create_index([("videoInfo.id", HASHED)], name="id");
		print("Video Info Database Set.")

class Videorel(object):
	""" Neo4j database to store the relation between videos.
		Relation has a attribute called weight. """

	def __init__(self):
		authenticate("localhost:7474", "YourTube", "pass")
		self.graph = Graph("http://localhost:7474/db/data/");

	def init_db(self):
		""" Create and populate the Neo4j database `video`. """
		print('Setting up Neo4j database. This will take some time.')
		files = os.listdir(os.getcwd() + '/database/video_info/')
		authenticate("localhost:7474", "YourTube", "pass")
		graph = Graph("http://localhost:7474/db/data/");

		data = [];

		for f in files:
			data_file = open(os.getcwd() + '/database/video_info/' + f);
			data.append(json.load(data_file));
			data_file.close();

		self.graph.run("MATCH (v) DETACH DELETE v");
		ids = [];
		data = data[0:50];
		for i in range(0,len(data)):
			d = data[i];
			rv = self.graph.run(
				"""
				CREATE (v:video 
				{ vid: '%s', commentCount: %s,
				viewCount: %s, favoriteCount: %s,
				dislikeCount: %s, likeCount: %s})
				RETURN ID(v);
				"""
				 % (str(d['videoInfo']['id']),
				str(d['videoInfo']['statistics']['commentCount']),
				str(d['videoInfo']['statistics']['viewCount']),
				str(d['videoInfo']['statistics']['favoriteCount']),
				str(d['videoInfo']['statistics']['dislikeCount']),
				str(d['videoInfo']['statistics']['likeCount'])) )
			x = 12;
			for record in rv:
				x = record;
			ids.append(x[u'ID(v)']);
			print(i);


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

					# Weight = weightage is the attribute of the relation.
					weightage = 100*(same_channel + percentage_desc_match + 2*percentage_tag_match);

					if (weightage > 0):
						self.graph.run(
							"""
							MATCH (v1:video), (v2:video)
							WHERE ID(v1) = %s AND ID(v2) = %s
							CREATE (v1)-[r2:WEIGHT {weight: %s}]->(v2);
							""" % (str(ids[i]), str(ids[j]), str(weightage)) )
			print(i)
		print("Relation between videos created.")

class UserDB(object):
	""" Setup the needed SQL tables. """
	def __init__(self):
		# Requires a 'user' database in which the tables are created.
		engine = create_engine(
			"mysql+pymysql://root:killthejoker@localhost/user?host=localhost?port=3306")
		engine.echo = True
		conn = engine.connect()
		metadata = MetaData(engine)
		userinfo = Table('userinfo', metadata,
			Column('user_id', Integer, primary_key=True),
			Column('videoid', String(30), primary_key=True),
			Column('latest_timestamp', String(30)),
			Column('viewCount', Integer),
			Column('likes', Integer),
			Column('dislikes', Integer),
			)

		usercred = Table('usercred', metadata,
			Column('user_id', Integer, primary_key=True),
			Column('password', String(30)),
			)
		metadata.create_all(engine)
		print('SQL tables set up.')
