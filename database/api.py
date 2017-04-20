""" Provide API for interacting with the database. """

import datetime as dt
import _mysql

from pymongo import *
from py2neo import *
from sqlalchemy import *
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import text
import time

# SQL
class UserDB(object):
	""" Superclass for all User database operations. """

	def __init__(self):
		self.engine = create_engine(
			"mysql+pymysql://root:root@localhost/user?host=localhost?port=3306")
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

class UserInfoDB(UserDB):
	""" Information about a user. """

	def __init__(self):
		super(UserInfoDB, self).__init__()
		Base = automap_base()
		Base.prepare(self.engine, reflect=True)
		self.UserInfoMap = Base.classes.userinfo
		self.userinfo = Table('userinfo', self.metadata, autoload=True)
		session = sessionmaker()
		session.configure(bind=self.engine)
		self.s = session()

	def upsert(self, username, vid, likes=0, dislikes=0):
		""" Update or insert the video stats accordingly. """		
		latest_timestamp = (dt.datetime.today()).strftime('%Y-%m-%d %H:%M:%S')
		record=self.s.query(self.UserInfoMap).filter_by(user_id=username,videoid=vid).first()
		if record is not None:
			record.latest_timestamp = latest_timestamp
			record.viewCount +=1
			record.likes=likes
			record.dislikes=dislikes
			self.s.commit()
		else:
			query = self.userinfo.insert()
			query.execute(user_id=username, videoid=vid, latest_timestamp=latest_timestamp,
				viewCount=0, likes=likes, dislikes=dislikes)
		return 1

	def get_user_info(self, username):
		record=self.s.query(self.UserInfoMap).filter_by(user_id=username).all()
		if record is None:
			return -1
		else:
			a = list()
			for r in record:
				a.append(r.videoid)
			return a

	def is_like(self, username, videoid):
		record=self.s.query(self.UserInfoMap).filter_by(user_id=username,videoid=videoid).all()
		if record is None:
			return 0
		else:
			for r in record:
				if r.likes==1:
					return 1
				elif r.dislikes == 1:
					return -1
				else:
					return 0

	def get_users_liked_video(self, username):
		record=self.s.query(self.UserInfoMap).filter_by(user_id=username, likes=1).all()
		if record is None:
			return -1
		else:
			a = list()
			b = list()
			for r in record:
				a.append(r.videoid)
				b.append(r.viewCount)
			return (a, b)


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
		self.collection.update_one(
			{ "videoid": str(videoid) },
			{ '$push': { "comments": {
			'$each': { "by": str(username), "timestamp": str(time), "comment": str(comment) } } } }
			)
		return 1

	def get_comments(self, videoid):
		res = self.collection.find_one( { "videoid": videoid } )
		if res is None:
			return -1
		else:
			return res['comments']


class VideoInfo(Video):
	""" To store the entire videoinfo. Initial scraped info. """
	
	def __init__(self):
		super(VideoInfo, self).__init__()
		self.collection = (self.db).video_info

	def get_video(self, videoid):
		res = self.collection.find_one({"videoInfo.id" : videoid})
		return res

	def search_text(self, query):
		""" Search the keywords of query (string) and return a list of video info
			in decreasing order of weight. """

		res = self.collection.find({"$text" : { "$search": query}}, { "score": { "$meta": "textScore" }})
		res.sort([('score', {'$meta': 'textScore'})])
		return res

	def get_tags(self, videoid):
		res = self.collection.find_one({"videoInfo.id" : videoid})
		return res['videoInfo']['snippet']['tags']


class HistoryTags(Video):
	""" To store tags accessed by this user in the past. """
	
	def __init__(self):
		super(HistoryTags, self).__init__()
		self.collection = (self.db).historytags

	def upsert_tag(self, username, tag, count=1):
		tag = tag.lower()
		res = self.collection.update_one(
			{"user_id":username, "tags.tag":tag},
			{ '$inc': {'tags.$.count':1} })
		if res.modified_count == 0:
			self.collection.update_one(
				{ "user_id": username },
				{'$push': { 'tags': {
				# '$each': { "tag": tag, "count": 1 } } } }
				"tag": tag, "count": 1 
				} } }
				)
		for i in range(0, count-1):
			self.collection.update_one(
			{"user_id":username, "tags.tag":tag},
			{ '$inc': {"tags.$.count"} })
		return 1

	def get_tags(self, username):
		res = self.collection.find_one({"user_id": username})
		if res is None:
			return -1
		else:
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
		MATCH (v1:video)-[r:WEIGHT]->(v2:video)
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
		MATCH (v1:video)-[r:WEIGHT]->(v2:video)
		WHERE v1.vid = '%s' AND v2.vid = '%s'
		RETURN r
		""" % (videoid1, videoid2, weight)
		res = self.graph.run(query)
		if res.rowcount == 0:
			# need to make this edge
			query = """
			MATCH (v1:video), (v2:video)
			WHERE v1.vid = %s AND v2.vid = %s
			CREATE (v1)-[r:WEIGHT {weight: %s}]->(v2);
			""" % (str(videoid1), str(videoid2), str(weight))
			self.graph.run(query)
			return
		# Else if edge already exists, then update the edge weight.
		# Get old weight. And add the increment to it.
		query = """
		MATCH (v1:video)-[r:WEIGHT]->(v2:video)
		WHERE v1.vid = '%s' AND v2.vid = '%s'
		RETURN r.weight
		""" % (videoid1, videoid2, weight)
		res = self.graph.run(query)
		original_weight = res.data()
		new_weight = original_weight + weight
		new_weight = str(new_weight)
		query = """
		MATCH (v1:video)-[r:WEIGHT]->(v2:video)
		WHERE v1.vid = '%s' AND v2.vid = '%s'
		SET r.weight = %s
		RETURN r
		""" % (videoid1, videoid2, new_weight)
		res = self.graph.run(query)
		return res

class UserGraph(object):
	def __init__(self):
		authenticate("localhost:7474", "YourTube", "pass")
		self.graph = Graph("http://localhost:7474/db/data/");

	def get_following_list(self, uid):
		""" Return list of userid of users which are being followed by this user """
		query = """
		MATCH (u1:user)-[r:follow]->(u2:user)
		WHERE u1.uid = '%s'
		RETURN u2.uid AS follows
		""" % (uid)
		res = self.graph.run(query)
		return res

	def follow_user(self, uid1, uid2):
		query = """
		MATCH (u1:user)-[r:follow]->(u2:user)
		WHERE u1.uid = '%s' And u2.uid = '%s'
		RETURN r
		""" % (uid1, uid2)		
		res = self.graph.run(query)
		if res.rowcount == 0:
			query = """
			MATCH (u1:user)-[r:follow]->(u2:user)
			WHERE u1.uid = '%s' And u2.uid = '%s'
			CREATE (u1) -[r:follow]-> (u2)
			RETURN r
			""" % (uid1, uid2)
			res = self.graph.run(query)

	def does_follow_user(uid1, uid2):
		query = """
		MATCH (u1:user)-[r:follow]->(u2:user)
		WHERE u1.uid = '%s' And u2.uid = '%s'
		RETURN r
		""" % (uid1, uid2)		
		res = self.graph.run(query)
		if res.rowcount == 0:
			return 0
		return 1

	def insert_user(uid1):
		query = """
		CREATE (u1:user {uid : '%s'})
		RETURN u1
		"""
		res = self.graph.run(query)

	def find_user(uid):
		query = """
		MATCH (u:user)
		WHERE u.uid = '%s'
		RETURN r
		""" % (uid)
		res = self.graph.run(query)
		if res.rowcount == 0:
			return 0
		return 1		