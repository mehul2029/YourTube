""" Provide API for interacting with the database. """

import datetime as dt
import _mysql

from pymongo import *
from py2neo import *
from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker
import time

# SQL
class UserDB(object):
	""" Superclass for all User database operations. """

	def __init__(self):
		self.engine = create_engine(
			"mysql+pymysql://root:killthejoker@localhost/user?host=localhost?port=3306")
		self.engine.echo = True
		self.conn = self.engine.connect()
		self.metadata = MetaData(self.engine)

class UserCredDB(UserDB):
	""" User Credentials. """

	def __init__(self):
		super(UserCredDB, self).__init__()
		self.user_cred = Table('usercred', self.metadata, autoload=True)

	def insert(self, username, passwd):
		""" Create a new user. Called for Signup. """
		
		# Check if username already exists
		query = self.user_cred.select(self.user_cred.c.user_id == username)
		query = query.execute()
		if(query.rowcount>0):
			return -1
		else:
			query = self.user_cred.insert()
			query.execute(user_id=username, password=passwd)
			return 1

	def authenticate(self, user, passwd):
		""" Authenticate a user. """
		
		query = self.user_cred.select(self.user_cred.c.user_id == username)
		if query.rowcount < 1:
			# No such user exists
			return -2
		elif query.rowcount == 1:
			if query['password'] != passwd:
				# Wrong password
				return -1
			else:
				# Successful
				return 1

class UserInfo(object):
	""" For session queries. """
	pass

class UserInfoDB(UserDB):
	""" Information about a user. """

	def __init__(self):
		super(UserInfoDB, self).__init__()
		self.userinfo = Table('userinfo', self.metadata, autoload=True)
		self.userinfo_mapper = mapper(UserInfo, self.userinfo)
		Session = sessionmaker(bind=self.engine)
		self.session = Session()

	def upsert(self, username, videoid, likes=0, dislikes=0):
		""" Update or insert the video stats accordingly. """
		
		latest_timestamp = (dt.datetime.today()).strftime('%Y-%m-%d %H:%M:%S')
		data = self.session.query(UserInfo).filter((self.userinfo.c.user_id==username) &
			(self.userinfo.c.videoid==videoid))
		if data.count() > 0:
			for instance in data:
				instance.latest_timestamp = latest_timestamp
				instance.viewCount += 1
				instance.likes = likes
				instance.dislikes = dislikes
				self.session.save(data)
				self.session.flush()
		else:
			query = self.userinfo.insert()
			query.execute(user_id=username, videoid=videoid, latest_timestamp=latest_timestamp,
				viewCount=0, likes=likes, dislikes=dislikes)
		return 1

	def get_user_info(self, username):
		query = self.userinfo.select([videoid]).where(userinfo.c.user_id==username)
		query = query.execute()
		if query.rowcount == 0:
			return -1
		return query

	def is_like(self, username, videoid):
		query = self.userinfo.select([likes, dislikes]).where(
			and_(userinfo.c.user_id==username, userinfo.c.videoid==videoid))
		query = query.execute()
		if query.rowcount == 0:
			return 0
		like = query['likes']
		dislike = query['dislikes']
		if like==1:
			return 1
		elif dislike == 1:
			return -1
		return 0	

# MONGODB
class Video(object):
	""" Superclass for videos stored in MongoDB. """
	
	def __init__(self):
		self.client = MongoClient()
		self.db = self.client.YourTube

	
class Comments(Video):
	""" To store user comments for videos."""

	def __init__(self):
		super(Comments, self).__init__()
		self.collection = (self.db).comments

	def add_comment(self, username, videoid, comment):
		time = dt.datetime.today()
		self.collection.update(
			{ "videoid": str(videoid) },
			{ '$push': { "comments": {
			'$each': { "by": str(username), "timestamp": str(time), "comment": str(comment) } } } }
			)
		return 1

	def get_comments(self, videoid):
		res = self.collection.find( { "videoid": videoid } )
		return res['comments']


class VideoInfo(Video):
	""" To store the entire videoinfo. Initial scraped info. """
	
	def __init__(self):
		super(VideoInfo, self).__init__()
		self.collection = (self.db).video_info

	def get_video(self, videoid):
		res = self.collection.find({"videoInfo.id" : videoid})
		return res

	def search_text(self, query):
		""" Search the keywords of query (string) and return a list of video info
			in decreasing order of weight. """

		res = self.collection.find({"$text" : { "$search": query}})
		return res

	def get_tags(self, videoid):
		res = self.collection.find({"videoInfo.id" : videoid})
		return res['videoInfo']['snippet']['tags']


class HistoryTags(Video):
	""" To store tags accessed by this user in the past. """
	
	def __init__(self):
		super(HistoryTags, self).__init__()
		self.collection = (self.db).historytags

	def upsert_tag(self, username, tag, count=1):
		tag = tag.lower()
		res = self.collection.update(
			{"user_id":username, "tags.tag":tag},
			{ '$inc': {"tags.$.count"} })
		if res.modified_count == 0:
			self.collection.update(
				{ "user_id": username },
				{'$push': { tags: {
				'$each': { "tag": tag, "count": 1 } } } }
				)
		for i in range(0, count-1):
			self.collection.update(
			{"user_id":username, "tags.tag":tag},
			{ '$inc': {"tags.$.count"} })
		return 1

	def get_tags(self, uername):
		res = self.collection.find({"user_id": username})
		return res['videoInfo']['snippet']['tags']

# NEO4J
class VideosGraph(object):
	""" Class for all Neo4j queries. """
	
	def __init__(self):
		authenticate("localhost:7474", "YourTube", "pass")
		self.graph = Graph("http://localhost:7474/db/data/");

	def get_neighbours(self, videoid, k=15):
		""" Get K nearest neighbours of the given node. Requires the videoid
			for search. """
		
		k = str(k)
		query = """
		MATCH (v1:video)-[r:WEIGHT]-(v2:video)
		WHERE v1.vid = '%s'
		WITH v2, r.weight AS sim
		ORDER BY sim DESC
		LIMIT %s
		RETURN v2.vid AS Neighbor, sim AS Similarity
		""" % (videoid, k)
		res = self.graph.run(query)
		return res

	def update_weight(self, videoid1, videoid2, weight):
		""" Update the weight of a relation between two videos. """
		# First if no edge exists, make a new edge.
		query = """
		MATCH (v1:video)-[r:WEIGHT]-(v2:video)
		WHERE v1.vid = '%s' AND v2.vid = '%s'
		RETURN r
		""" % (videoid1, videoid2, weight)
		res = self.graph.run(query)
		if query.rowcount == 0:
			# need to make this edge
			query = """
			MATCH (v1:video), (v2:video)
			WHERE v1.vid = %s AND v2.vid = %s
			CREATE (v1)-[r:WEIGHT {weight: %s}]->(v2);
			""" % (str(videoid1), str(videoid2), str(weight))
			return
		# Else if edge already exists, then update the edge weight.
		# Get old weight. And add the increment to it.
		query = """
		MATCH (v1:video)-[r:WEIGHT]-(v2:video)
		WHERE v1.vid = '%s' AND v2.vid = '%s'
		RETURN r.weight
		""" % (videoid1, videoid2, weight)
		res = self.graph.run(query)
		original_weight = res.data()
		new_weight = original_weight + weight
		new_weight = str(new_weight)
		query = """
		MATCH (v1:video)-[r:WEIGHT]-(v2:video)
		WHERE v1.vid = '%s' AND v2.vid = '%s'
		SET r.weight = %s
		RETURN r
		""" % (videoid1, videoid2, new_weight)
		res = self.graph.run(query)
		return res
